package ShellTokens;
# Shared by commit_args_ok.pl and dispatch_brief.pl: split a shell command into tokens, and
# report quoting forms the tokenizer cannot read. Not a shell parser; callers fail closed.
use strict; use warnings;
use Text::ParseWords qw(shellwords parse_line);
use Exporter 'import';
our @EXPORT_OK = qw(tokens unreadable fold_continuations skeleton $control $redirect);

our $control  = qr/^(?:;|&&|\|\||\||&|\))$/;
our $redirect = qr/^\d*(?:>>?|<|>&|<&)/;

# A plain token with a separator glued on (`m;`, `x&&`) is split so the separator ends the command
# instead of reading as a pathspec; tokens with quotes or backslashes are left whole.
sub tokens {
  my ($cmd) = @_;
  my @t;
  for my $raw (parse_line('\s+', 1, $cmd)) {
    next unless defined $raw && length $raw;
    if ($raw !~ /['"\\]/ && $raw =~ /^(.+?)(;|&&|\|\|)$/) { push @t, $1, $2 }
    else { push @t, shellwords($raw) }
  }
  return @t;
}

# Returns a short reason when the command holds a form the tokenizer cannot read, else ''.
# Single-quoted text is literal. Outside single quotes: an unbalanced quote, a backtick, $(...),
# $'...' and (unquoted only) a heredoc marker are unreadable.
sub unreadable {
  my ($c) = @_;
  $c =~ s/\s+\z//;   # a trailing newline ends the command
  my ($q, $n) = ('', length $c);
  for (my $i = 0; $i < $n; $i++) {
    my $ch = substr($c, $i, 1);
    my $nx = $i + 1 < $n ? substr($c, $i + 1, 1) : '';
    if ($q eq "'") { $q = '' if $ch eq "'"; next }
    if ($ch eq '\\') { $i++; next }
    return 'backtick' if $ch eq '`';
    return 'command substitution' if $ch eq '$' && $nx eq '(';
    if ($q eq '"') { $q = '' if $ch eq '"'; next }
    return 'newline between commands' if $ch eq "\n";
    return "ANSI-C quote" if $ch eq '$' && $nx eq "'";
    return 'heredoc' if $ch eq '<' && $nx eq '<';
    $q = $ch if $ch eq "'" || $ch eq '"';
  }
  return 'unbalanced quote' if $q ne '';
  return '';
}

# Removes backslash-newline line continuations outside single quotes (inside them they are literal).
sub fold_continuations {
  my ($c) = @_;
  my ($q, $o, $n) = ('', '', length $c);
  for (my $i = 0; $i < $n; $i++) {
    my $ch = substr($c, $i, 1);
    if ($q eq "'") { $q = '' if $ch eq "'"; $o .= $ch; next }
    if ($ch eq '\\') {
      my $nx = $i + 1 < $n ? substr($c, $i + 1, 1) : '';
      if ($nx eq "\n") { $i++; next }
      $o .= $ch . $nx; $i++; next;
    }
    if ($q eq '"') { $q = '' if $ch eq '"' }
    elsif ($ch eq "'" || $ch eq '"') { $q = $ch }
    $o .= $ch;
  }
  return $o;
}

# The command with text that cannot run removed, for a caller that looks for real tokens (cd, -C ...).
# Single-quoted contents and heredoc bodies are dropped. Double-quoted contents are dropped only until
# the first double-quoted string holding $( or a backtick: that string is kept, and so is all quoted
# text after it. Not a parser: no nesting, no escapes beyond backslash. A quote it cannot close
# returns the raw text, so the caller fails closed.
sub skeleton {
  my ($c) = @_;
  my ($o, $n, $drop, $st, @pend) = ('', length $c, 1, 'code');
  for (my $i = 0; $i < $n; ) {
    my $ch = substr($c, $i, 1);
    if ($ch eq "\n" && @pend) {   # heredoc bodies start on the next line
      $o .= "\n"; $i++;
      for my $p (@pend) {
        while ($i < $n) {
          my $e = index($c, "\n", $i); $e = $n if $e < 0;
          my $l = substr($c, $i, $e - $i); $i = $e < $n ? $e + 1 : $n;
          $l =~ s/^\t+// if $p->[1];
          last if $l eq $p->[0];
        }
      }
      @pend = (); next;
    }
    if ($ch eq '\\' && $st ne 'sq') { $o .= substr($c, $i, 2); $i += 2; next }
    if ($st eq 'sq') { $st = 'code' if $ch eq "'"; $o .= $ch if !$drop || $ch eq "'"; $i++; next }
    if ($st eq 'dq') { $st = 'code' if $ch eq '"'; }
    elsif ($ch eq "'") { $st = 'sq'; $o .= "'" ; $i++; next }
    elsif ($ch eq '"') {
      if ($drop) {
        my $j = $i + 1; $j += substr($c, $j, 1) eq '\\' ? 2 : 1 while $j < $n && substr($c, $j, 1) ne '"';
        return $c if $j >= $n;
        my $in = substr($c, $i + 1, $j - $i - 1);
        if (index($in, '$(') < 0 && index($in, '`') < 0) { $o .= '""'; $i = $j + 1; next }
        $drop = 0;
      }
      $st = 'dq'; $o .= '"'; $i++; next;
    }
    if ($ch eq '<' && substr($c, $i + 1, 1) eq '<') {
      if (substr($c, $i + 2, 1) eq '<') { $o .= '<<<'; $i += 3; next }
      pos($c) = $i;
      if ($c =~ /\G<<(-?)[ \t]*(?:'([^']*)'|"([^"]*)"|(\w+))/gc) {
        push @pend, [$+, $1 eq '-'];
        $o .= substr($c, $i, pos($c) - $i); $i = pos($c); next;
      }
    }
    $o .= $ch; $i++;
  }
  return $c if $st ne 'code';
  return $o;
}

1;
