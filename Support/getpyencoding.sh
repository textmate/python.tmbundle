#!/bin/sh
perl < "$1" -pe 's/\s*#.*?coding[=:]\s*([-\w.]+).*|.*(\n)?/$1/' | head -1
