#!/bin/bash

# --- НАСТРОЙКИ ---
# Имя твоего файла БЕЗ расширения .tex
PROJECT="main"
# -----------------

if [ "$1" = "run" ]; then
    echo "🚀 Compiling presentation: $PROJECT..."
    
    # Запускаем latexmk с XeLaTeX
    # -synctex=1 : позволяет прыгать из PDF в код и обратно (cmd+click)
    # -interaction=nonstopmode : не останавливаться на каждой ошибке, а показывать их в конце
    # -file-line-error : показывает ошибки в формате "файл:строка:ошибка" (удобно для VS Code)
    latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error "$PROJECT.tex"
    
    # Опционально: открыть PDF сразу после успешной сборки (только для macOS)
    if [ $? -eq 0 ]; then
        echo "✅ Build success!"
        # open "$PROJECT.pdf" 
    else
        echo "❌ Build failed!"
    fi

elif [ "$1" = "clean" ]; then
    echo "🧹 Cleaning up..."
    
    # 1. Штатная очистка через latexmk (удаляет основные временные файлы)
    latexmk -c "$PROJECT.tex"

    # 2. Дополнительная "жесткая" очистка специфических файлов
    # Важно: я изменил логику find. Твой старый скрипт удалял ВСЕ pdf в папке.
    # Этот удаляет только файлы, относящиеся к текущему проекту.
    
    # Удаляем специфичные для Beamer файлы (.nav, .snm, .vrb) и остальные
    rm -f "$PROJECT.nav" "$PROJECT.snm" "$PROJECT.vrb" \
          "$PROJECT.bbl" "$PROJECT.blg" "$PROJECT.fls" \
          "$PROJECT.fdb_latexmk" "$PROJECT.synctex.gz" \
          "$PROJECT.xdv" "$PROJECT.toc" "$PROJECT.aux" \
          "$PROJECT.log" "$PROJECT.out"

    # Если хочешь удалять и итоговый PDF при очистке, раскомментируй строку ниже:
    rm -f "$PROJECT.pdf"
    
    echo "✨ Cleaned."

else
    echo "Usage: $0 {run|clean}"
    echo "  run   : Build the PDF using XeLaTeX"
    echo "  clean : Remove temporary files (including Beamer-specific files)"
    exit 1
fi