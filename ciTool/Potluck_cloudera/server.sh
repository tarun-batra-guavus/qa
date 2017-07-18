#!/bin/sh

# Just a placeholder for the actual ui server
# An attempt of keeping all actual code in src directory

dir=`dirname $0`
python ${dir}/src/ui_server.py "$@"
