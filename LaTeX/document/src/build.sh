#!/bin/bash

if [ "$1" = "run" ]; then
    latexmk -xelatex main.tex
elif [ "$1" = "clean" ]; then
    latexmk -c
    find . -type f -name "*.aux" -o -name "*.bbl" -o -name "*.blg" -o -name "*.fdb_latexmk" -o -name "*.fls" -o -name "*.log" -o -name "*.synctex.gz" -o -name "*.toc" -o -name "*.xdy" -o -name "*.pdf" -o -name "*.glo*" -o -name "*.xdv" -o -name "main.run.xml" | xargs rm -f
else
    echo "Usage: $0 {run|clean}"
    echo "  run: Build the PDF"
    echo "  clean: Remove temporary files"
    exit 1
fi