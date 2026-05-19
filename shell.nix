{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    pkg-config
    sqlite
    raylib
    glfw
    libGL
    xorg.libX11
    xorg.libXrandr
    xorg.libXi
    xorg.libXinerama
    xorg.libXcursor
    wineWowPackages.full   # <-- adicionado para Wine 64 bits
    python3Minimal         # <-- opcional, mas útil
    unzip   # <--- adicione esta linha
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.lib.makeLibraryPath [
      pkgs.raylib
      pkgs.glfw
      pkgs.libGL
      pkgs.xorg.libX11
      pkgs.xorg.libXrandr
      pkgs.xorg.libXi
      pkgs.xorg.libXinerama
      pkgs.xorg.libXcursor
    ]}:$LD_LIBRARY_PATH

    if [ ! -d ".venv" ]; then
      python -m venv .venv
    fi
    source .venv/bin/activate
    pip install --upgrade pip
    pip install raylib

    echo "Ambiente pronto. Para gerar .exe: ./build_windows_exe.sh"
  '';
}
