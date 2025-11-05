#!/bin/bash

if [ "$1" = "run" ]; then
    latexmk -xelatex main.tex
elif [ "$1" = "clean" ]; then
    latexmk -c
else
    echo "Usage: $0 {run|clean}"
    echo "  run: Build the PDF"
    echo "  clean: Remove temporary files"
    exit 1
fi