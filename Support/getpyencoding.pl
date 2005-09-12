#!/usr/bin/perl

# Copyright (c) Domenico Carbotta, 2005
# This code is released under the GNU General Public License.

my $lineno = 0;

while (<>) {
    last if $lineno++ > 2;
    if (/\s*#.*?coding[:=]\s*([-\w.]+)/) {
        print $1;
        last;
    }
}
