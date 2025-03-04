{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShell {
  # Specify the packages you want in the environment
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.pip
    pkgs.python3Packages.virtualenv
    pkgs.libcdada
    pkgs.libgcc
    pkgs.chromedriver
    pkgs.chromium
  ];

  env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.libz
    pkgs.chromedriver
  ];

  # Optional: Set environment variables
  shellHook = ''
    # Create a virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
      python -m venv venv
    fi

    # Activate the virtual environment
    source venv/bin/activate

    # Upgrade pip to the latest version
    pip install --upgrade pip

    echo "Virtual environment activated. Use 'pip install <package>' to install Python libraries."
    pip3 install gnews
    pip3 install newspaper3k
  '';
}
