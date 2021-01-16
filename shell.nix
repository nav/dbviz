{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
  buildInputs = [
    pkgs.graphviz
    pkgs.pipenv
    pkgs.python39
    pkgs.python39Packages.mysqlclient
  ];

  shellHooks = ''
    export PIP_PREFIX="$(pwd)/.venv"
    export PYTHONPATH="$PIP_PREFIX/${pkgs.python39.sitePackages}:$PYTHONPATH"
    export PATH="$PIP_PREFIX/bin:$PATH"
    export LD_LIBRARY_PATH="${lib.makeLibraryPath [ zlib stdenv.cc.cc.lib ]}:${stdenv.cc.cc.lib}/lib64"
    export PIPENV_VENV_IN_PROJECT=1
    export PIP_IGNORE_INSTALLED=1
    export PIP_NO_CACHE_DIR=true
    unset SOURCE_DATE_EPOCH
  '';
}
