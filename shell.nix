{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # System dependencies
    pkg-config
    sqlite
    
    # Graphics & Raylib
    raylib
    glfw
    libGL
    xorg.libX11
    xorg.libXrandr
    xorg.libXi
    xorg.libXinerama
    xorg.libXcursor
    
    # Python environment
    (python3.withPackages (ps: with ps; [
      pip
    ]))
  ];

  shellHook = ''
    # Setup LD_LIBRARY_PATH so pyray can find the installed raylib shared library
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

    # Optional: Set up a virtual environment automatically
    if [ ! -d ".venv" ]; then
      python -m venv .venv
    fi
    source .venv/bin/activate
    
    # Ensure dependencies are installed
    pip install --upgrade pip
    pip install raylib
    
    echo "Python UI development environment ready."
    echo "To run your UI: python search_ui.py"
  '';
}
