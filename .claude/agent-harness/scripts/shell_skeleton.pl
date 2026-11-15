#!/usr/bin/env perl
# Reads a shell command on stdin, prints it with quoted text and heredoc bodies removed (ShellTokens::skeleton).
use strict; use warnings;
use FindBin;
use lib $FindBin::Bin;
use ShellTokens qw(skeleton);
print skeleton(do { local $/; <STDIN> } // '');
