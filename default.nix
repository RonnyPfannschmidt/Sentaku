with import <nixpkgs> {};
with pkgs;
with python27Packages;
stdenv.mkDerivation rec {
  name = "sentaku-test";
  src = ./.;
  buildInputs = [
    gitFull
    less
    ncurses
    openssh
    bpython
    sqlite
    setuptools_scm
    pip
    tox
    wheel
    pytest
    flake8
    pygments
    sphinx
    requests
    selenium
    virtualenv
    watchdog
  ];

  shellHook=''
  export PS1="(${name}) \w \\$ \[$(tput sgr0)\]"
  export PYTHONPATH="$PYTHONPATH:./src"


  build_docs() {
    sphinx-build -b html -d build/sphinx-doctrees docs build/htmldocs
  }

  autobuild_docs() {
    watchmedo shell-command docs src -R \
      -c 'sphinx-build -b html -d build/sphinx-doctrees docs build/htmldocs'
  }

  clean() {
    find -name \*.pyc -delete
    find -name __pycache__ -delete
    rm -rf build/sphinx-doctrees build/htmldocs
  }

  build_fresh_docs() {
    clean
    build_docs
  }

  test_clean() {
    clean
    py.test
  }

  '';
}
