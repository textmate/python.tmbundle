#!/usr/bin/perl

# A glorified one-liner. Yay for language promiscuity!

while (<>) {
    last if $. > 2;
    if (/\s*#.*?coding[:=]\s*([-\w.]+)/) {
        print $1;
        last;
    }
}
