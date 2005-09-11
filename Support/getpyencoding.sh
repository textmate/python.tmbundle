#!/bin/sh
perl < "$1" -pe 's/\s*#.*?coding[=:]\s*([-\w.]+).*/$1/' | head -1
