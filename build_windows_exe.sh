#!/usr/bin/env bash
# build_windows_exe.sh - versão corrigida (sem cmd /c e usando bsdtar)

set -x
set -e

WINEPREFIX="$HOME/.wine_rca"
WINEARCH="win64"
PYTHON_VERSION="3.10.11"
PYTHON_INSTALLER="python-${PYTHON_VERSION}-amd64.exe"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_INSTALLER}"
RAYLIB_URL="https://github.com/raysan5/raylib/releases/download/6.0/raylib-6.0_win64_msvc16.zip"

export WINEPREFIX="$WINEPREFIX"
export WINEARCH="$WINEARCH"

# Baixa raylib.dll se não existir (usando bsdtar, nativo no NixOS)
if [ ! -f "raylib.dll" ]; then
    echo "Baixando raylib 6.0 para Windows..."
    wget -q --show-progress "$RAYLIB_URL" -O raylib-6.0_win64_msvc16.zip
    bsdtar -xf raylib-6.0_win64_msvc16.zip   # <-- substitui unzip
    cp raylib-6.0_win64_msvc16/lib/raylib.dll .
    rm -rf raylib-6.0_win64_msvc16 raylib-6.0_win64_msvc16.zip
fi

# Cria prefixo Wine se não existir
if [ ! -d "$WINEPREFIX" ]; then
    echo "Criando prefixo Wine 64 bits..."
    wineboot -u
    sleep 3
fi

# Baixa instalador Python se não existir
if [ ! -f "$PYTHON_INSTALLER" ]; then
    echo "Baixando Python $PYTHON_VERSION para Windows..."
    wget -q --show-progress "$PYTHON_URL"
fi

# Instala Python (silencioso) se ainda não estiver instalado
if ! wine cmd /c "python --version" 2>/dev/null | grep -q "$PYTHON_VERSION"; then
    echo "Instalando Python no Wine (pode demorar)..."
    wine "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1
    sleep 5
fi

# Instala pyinstaller e raylib via pip
echo "Instalando dependências Python (pyinstaller, raylib)..."
wine pip install --upgrade pip
wine pip install pyinstaller raylib

# Cria diretório do projeto dentro do Wine
PROJECT_DIR="$WINEPREFIX/drive_c/projeto_rca"
mkdir -p "$PROJECT_DIR"

# Copia ui.py e a DLL baixada para o projeto
cp ui.py "$PROJECT_DIR/"
cp raylib.dll "$PROJECT_DIR/"

# Gera o .exe com PyInstaller (execução direta, sem cmd /c problemático)
echo "Gerando executável (pode levar alguns minutos)..."
cd "$PROJECT_DIR"
wine pyinstaller --onefile --name ui --add-data "raylib.dll;." ui.py
cd - > /dev/null

# Copia o .exe gerado para o diretório atual
cp "$PROJECT_DIR/dist/ui.exe" .

echo "SUCESSO! Executável gerado: ./ui.exe"
echo "Para testar com Wine: wine ./ui.exe"
