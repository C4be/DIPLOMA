#!/bin/bash

echo "Найдены следующие папки __pycache__:"
find . -type d -name "__pycache__"

echo ""
read -p "Вы уверены, что хотите удалить эти папки? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    find . -type d -name "__pycache__" -exec rm -rf {} +
    echo "Папки __pycache__ удалены"
else
    echo "Операция отменена"
fi