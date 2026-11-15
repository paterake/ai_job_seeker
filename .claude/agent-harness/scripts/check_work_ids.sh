#!/usr/bin/env bash
# PreToolUse (Bash, if "git *"): deny a commit whose staged diff ADDS a line matching a
# repo-supplied work-id pattern. Patterns come from the staged .pco/work_id_patterns.json; the
# harness ships none. Own hook entry, separate from gate_commit.sh, so a bug here cannot trip
# that script's fail-closed trap. Config errors fail closed only once the repo config is in the index;
# a hook crash, timeout or start failure blocks every git command in every repo (onFailure: block on Bash(git *)).
set -uo pipefail

GATE_TOOL=check_work_ids
sid=""; tree=""

payload="$(cat)" || exit 0
cwd="$(printf '%s' "$payload" | jq -r '.cwd // empty')" || exit 0
cmd="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')" || exit 0
sid="$(printf '%s' "$payload" | jq -r '.session_id // empty')" || sid=""
grep -Eq '(^|[;&|(`[:space:]])git([[:space:]]+(-[cC]|--(namespace|config-env|shallow-file|attr-source|git-dir|work-tree))[[:space:]]+[^[:space:]]+|[[:space:]]+-[^[:space:]]+)*[[:space:]]+commit([[:space:]]|$)' <<<"$cmd" || exit 0
. "$(dirname "$0")/gate_deny.sh" || { printf 'gate: gate_deny.sh missing, refused (fail closed)\n' >&2; exit 2; }

root="$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)" || { tel allowed not_a_repo; exit 0; }   # gate_commit.sh denies this case
cfgpath=".pco/work_id_patterns.json"
if ! git -C "$root" cat-file -e ":$cfgpath" 2>/dev/null; then
  echo "work-id lint: no $cfgpath staged, not checked" >&2
  tel allowed not_opted_in
  exit 0
fi

# From here the repo has opted in: any error refuses the commit.
trap 'deny "WORK-ID LINT: lint error, commit refused (fail closed)." script_error' ERR

cfg="$(git -C "$root" show ":$cfgpath")"

read -r -d '' PL <<'PERL' || true
use strict; use warnings; use JSON::PP;
sub fail { print "$_[0]\n"; exit 3 }
my $f = ".pco/work_id_patterns.json";
my $cfg = eval { decode_json($ENV{WID_CFG}) };
fail("$f is not valid JSON") unless ref $cfg eq 'HASH';
my $pats = $cfg->{patterns};
fail("$f needs a non-empty 'patterns' list") unless ref $pats eq 'ARRAY' && @$pats;
my @P;
for my $p (@$pats) {
  fail("$f: every pattern needs string 'id' and 'regex'")
    unless ref $p eq 'HASH' && defined $p->{id} && !ref $p->{id} && length $p->{id}
      && defined $p->{regex} && !ref $p->{regex} && length $p->{regex};
  my $re = eval { qr/$p->{regex}/ };
  fail("$f: pattern '$p->{id}' regex does not compile in Perl") unless $re;
  push @P, [$p->{id}, $re];
}
my %ext;
if (defined $cfg->{extensions}) {
  fail("$f: 'extensions' must be a list of strings") unless ref $cfg->{extensions} eq 'ARRAY';
  for my $e (@{$cfg->{extensions}}) { (my $x = $e) =~ s/^\.//; $ext{lc $x} = 1 }
}
sub glob2re {
  my ($g) = @_; my $o = '';
  while (length $g) {
    if ($g =~ s{^\*\*/}{}) { $o .= '(?:.*/)?' }
    elsif ($g =~ s{^\*\*}{}) { $o .= '.*' }
    elsif ($g =~ s{^\*}{}) { $o .= '[^/]*' }
    elsif ($g =~ s{^\?}{}) { $o .= '[^/]' }
    else { $g =~ s{^(.)}{}s; $o .= quotemeta($1) }
  }
  return qr/^$o$/;
}
my @A;
if (defined $cfg->{allow}) {
  fail("$f: 'allow' must be a list") unless ref $cfg->{allow} eq 'ARRAY';
  for my $a (@{$cfg->{allow}}) {
    fail("$f: every allow entry needs a 'glob'") unless ref $a eq 'HASH' && defined $a->{glob} && !ref $a->{glob};
    my %ids;
    if (defined $a->{patterns}) {
      fail("$f: allow 'patterns' must be a list of ids") unless ref $a->{patterns} eq 'ARRAY';
      $ids{$_} = 1 for @{$a->{patterns}};
    }
    push @A, [glob2re($a->{glob}), defined $a->{patterns} ? \%ids : undef];
  }
}
my ($path, $inhunk, $ln, @hits, $n) = (undef, 0, 0);
$n = 0;
while (my $l = <STDIN>) {
  chomp $l;
  if ($l =~ /^diff --git /) { $inhunk = 0; $path = undef; next }
  if (!$inhunk) {
    if ($l =~ m{^\+\+\+ b/(.*?)\t?$}) { $path = $1; next }
    if ($l =~ m{^\+\+\+ "b/(.*)"$}) { $path = $1; next }
    if ($l =~ /^\+\+\+ \/dev\/null/) { $path = undef; next }
    if ($l =~ /^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/) { $ln = $1; $inhunk = 1 }
    next;
  }
  if ($l =~ /^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/) { $ln = $1; next }
  if ($l =~ /^\+(.*)$/) {
    my $t = $1; my $cur = $ln++;
    next unless defined $path;
    if (%ext) { my ($e) = $path =~ /\.([^.\/]+)$/; next unless defined $e && $ext{lc $e} }
    my ($all, %skip) = (0);
    for my $a (@A) { next unless $path =~ $a->[0]; if (defined $a->[1]) { $skip{$_} = 1 for keys %{$a->[1]} } else { $all = 1 } }
    next if $all;
    for my $p (@P) {
      next if $skip{$p->[0]};
      if ($t =~ $p->[1]) {
        $n++;
        if (@hits < 10) { (my $s = $t) =~ s/^\s+|\s+$//g; $s = substr($s, 0, 120); push @hits, "$path:$cur matches $p->[0]: $s" }
        last;
      }
    }
  }
}
if ($n) {
  my $m = "WORK-ID LINT: " . join("; ", @hits);
  $m .= "; plus " . ($n - @hits) . " more" if $n > @hits;
  $m .= ". Name what the thing is instead of its work id, and put provenance in the commit message.";
  fail($m);
}
PERL

diff_out="$(git -C "$root" -c core.quotePath=false diff --cached -U0 --no-color --no-ext-diff --diff-filter=d)"
rc=0
out="$(printf '%s\n' "$diff_out" | WID_CFG="$cfg" perl -MJSON::PP -e "$PL")" || rc=$?
case "$rc" in
  0) tel allowed clean; exit 0 ;;
  3) case "$out" in "WORK-ID LINT:"*) code=work_id_found ;; *) code=config_invalid ;; esac
     deny "$out" "$code" ;;
  *) deny "WORK-ID LINT: lint error, commit refused (fail closed)." script_error ;;
esac
