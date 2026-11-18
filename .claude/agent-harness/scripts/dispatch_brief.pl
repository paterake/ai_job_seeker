#!/usr/bin/env perl
# Reads a shell command on stdin. Finds the one `claude ... --bg` or `--background` segment (up to the next control
# operator) and prints its brief, the last positional argument whatever the flag order, then exit 0.
# Exit 1 (reason on stdout) when the brief cannot be read: unbalanced quotes, $(...), backticks,
# $'...', a heredoc, @file, no positional argument, or more than one `claude --bg` or `--background` segment.
use strict; use warnings;
use FindBin;
use lib $FindBin::Bin;
use ShellTokens qw(tokens unreadable fold_continuations $control $redirect);

sub unread { print "$_[0]"; exit 1 }

my $cmd = do { local $/; <STDIN> } // '';
if (my $why = unreadable($cmd)) { unread($why) }
my @t = tokens(fold_continuations($cmd));
unread('no tokens') unless @t;

# Flags that take a separate value (claude --help); --flag=value is one token.
my %value = map { $_ => 1 } qw(--add-dir --agent --agents --append-system-prompt --autocompact --betas
  --debug-file --effort --environment --fallback-model --file --input-format --json-schema
  --max-budget-usd --mcp-config --model -n --name --output-format --permission-mode
  --permission-prompts --plugin-dir --plugin-url --session-id --setting-sources --settings
  --system-prompt --system-prompt-snapshot --tools --allowedTools --allowed-tools
  --disallowedTools --disallowed-tools --resume -r);

my @briefs;
for (my $i = 0; $i < @t; $i++) {
  next unless $t[$i] =~ /(?:^|[;&|(`])claude$/;
  my ($bg, @pos) = (0);
  my $k;
  for ($k = $i + 1; $k < @t; $k++) {
    my $a = $t[$k];
    last if $a =~ $control;
    if ($a =~ $redirect) { $k++ if $a =~ /^\d*(?:>>?|<<-?|<|>&|<&)$/; next }
    if ($a eq '--bg' || $a eq '--background') { $bg = 1; next }
    if ($a =~ /^-/ && $a ne '-') { $k++ if $value{$a}; next }
    push @pos, $a;
  }
  $i = $k;
  next unless $bg;
  unread('no positional brief') unless @pos;
  unread('@file argument') if $pos[-1] =~ /^@/;
  push @briefs, $pos[-1];
}
unread('no claude --bg or --background segment') unless @briefs;
unread('more than one claude --bg or --background segment') if @briefs > 1;
print $briefs[0];
exit 0;
