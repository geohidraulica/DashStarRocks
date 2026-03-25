#!/bin/bash

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Iniciando Dash con Gunicorn..."
gunicorn app:server --bind 0.0.0.0:${PORT:-10000}