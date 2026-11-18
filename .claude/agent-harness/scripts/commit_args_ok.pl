#!/usr/bin/env perl
# Reads a shell command on stdin. Exit 0 if every `git commit` in it commits exactly the staged
# tree; exit 1 (reason on stdout) for -a/--all, -i/--include, -o/--only, -p/--patch,
# --interactive, --pathspec-from-file, or a pathspec; exit 2 if the command cannot be parsed.
use strict; use warnings;
use FindBin;
use lib $FindBin::Bin;
use ShellTokens qw(tokens $control $redirect);

my $cmd = do { local $/; <STDIN> } // '';
my @t = tokens($cmd);
if (!@t && $cmd =~ /\S/) { print "cannot parse the command"; exit 2; }

# git accepts any unique prefix of a long option, so match by prefix.
my @bad_long   = qw(all include only patch interactive pathspec-from-file pathspec-file-nul);
my @value_long = qw(message file reuse-message reedit-message author date template cleanup
  fixup squash trailer);
my $is_prefix  = sub { my ($n, @full) = @_; grep { index($_, $n) == 0 } @full };

sub refuse { print "git commit $_[0]"; exit 1 }

for (my $i = 0; $i < @t; $i++) {
  next unless $t[$i] =~ /(?:^|[;&|(`])(?:[^\s;&|(`]*\/)?git$/;
  my $j = $i + 1;
  while ($j < @t && $t[$j] =~ /^-/) { $j += ($t[$j] =~ /^(?:-[cC]|--(?:namespace|config-env|shallow-file|attr-source|git-dir|work-tree))$/) ? 2 : 1 }   # global options; value options take an argument
  next unless $j < @t && $t[$j] eq 'commit';
  for (my $k = $j + 1; $k < @t; $k++) {
    my $a = $t[$k];
    last if $a =~ $control;
    # Redirections (heredoc markers included) are skipped, plus a separate target; scanning goes
    # on, so a heredoc body is read as pathspecs and refused (fails closed).
    if ($a =~ $redirect) { $k++ if $a =~ /^\d*(?:>>?|<<-?|<|>&|<&)$/; next }
    if ($a eq '--') { refuse('-- <pathspec>') if $k + 1 < @t && $t[$k + 1] !~ $control; last }
    if ($a =~ /^--([^=]+)/) {
      my $n = $1;
      refuse("--$n") if $is_prefix->($n, @bad_long);
      $k++ if $a !~ /=/ && $is_prefix->($n, @value_long);
      next;
    }
    if ($a =~ /^-(.+)$/) {                                 # short-flag cluster, e.g. -am
      my @c = split //, $1;
      for my $x (0 .. $#c) {
        refuse("-$c[$x]") if $c[$x] =~ /[aiop]/;
        last if $c[$x] =~ /[Su]/;                          # optional value, attached only
        if ($c[$x] =~ /[mFCct]/) { $k++ if $x == $#c; last }   # value: attached, or next token
      }
      next;
    }
    refuse("<pathspec> ($a)");
  }
}
exit 0;
