#!/usr/bin/env bash
# build_windows_32bit.sh - Forçando ambiente 32-bit consistente

set -x
set -e

# Define um prefixo específico para 32-bit
WINEPREFIX="$HOME/.wine_32bit_rca"
WINEARCH="win32"
PYTHON_VERSION="3.10.11"
# Baixe a versão 32-bit do Python (sem o -amd64)
PYTHON_INSTALLER="python-${PYTHON_VERSION}.exe"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_INSTALLER}"
# URL da Raylib 32-bit que você forneceu
RAYLIB_URL="https://github.com/raysan5/raylib/releases/download/6.0/raylib-6.0_win32_msvc16.zip"

export WINEPREFIX="$WINEPREFIX"
export WINEARCH="$WINEARCH"

# 1. Configura o prefixo Wine 32-bit
if [ ! -d "$WINEPREFIX" ]; then
    echo "Criando prefixo Wine 32-bit..."
    wineboot -u
fi

# 2. Baixa raylib.dll 32-bit
if [ ! -f "raylib.dll" ]; then
    echo "Baixando raylib 32-bit..."
    wget -q "$RAYLIB_URL" -O raylib.zip
    bsdtar -xf raylib.zip
    cp raylib-6.0_win32_msvc16/lib/raylib.dll .
    rm -rf raylib-6.0_win32_msvc16 raylib.zip
fi

# 3. Baixa Python 32-bit (se não existir)
if [ ! -f "$PYTHON_INSTALLER" ]; then
    wget -q "$PYTHON_URL"
fi

# 4. Instala Python 32-bit no Wine
wine "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1

# 5. Instala dependências
wine python -m pip install --upgrade pip
wine python -m pip install pyinstaller raylib

# 6. Gera o .exe 32-bit
PROJECT_DIR="$WINEPREFIX/drive_c/projeto_rca"
mkdir -p "$PROJECT_DIR"
cp ui.py raylib.dll "$PROJECT_DIR/"

cd "$PROJECT_DIR"
wine python -m PyInstaller --onefile --hidden-import sqlite3 --name ui --add-data "raylib.dll;." ui.py
cd -

cp "$PROJECT_DIR/dist/ui.exe" .
echo "SUCESSO! Executável 32-bit gerado."
