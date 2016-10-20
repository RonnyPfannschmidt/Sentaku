with import <nixpkgs> {};
with pkgs;
with python27Packages;
let
  dectate = buildPythonPackage rec {
    name = "dectate-${version}";
    version = "0.12";
    src = fetchurl {
      url = "mirror://pypi/d/dectate/${name}.tar.gz";
      sha256="14hc65695r89x1ivm1gj3dcvsn2mk6a5ax01sl7s5cp1nyj8bfd3";
    };
  };
in buildPythonPackage rec {
  name = "sentaku-test";
  src = ./.;
  buildInputs = [
    setuptools_scm
    pytest
    flake8
    sphinx
    requests
    selenium
  ];

  propagatedBuildInputs = [dectate attrs];

  shellHook=''
  export PS1="(${name}) \w \\$ \[$(tput sgr0)\]"
  export PYTHONPATH="$PYTHONPATH:./src"
  test() {
    py.test
  }

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
    test
  }

  '';
}
