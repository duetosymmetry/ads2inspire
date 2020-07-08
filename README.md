[![github](https://img.shields.io/badge/GitHub-ads2inspire-blue.svg)](https://github.com/duetosymmetry/ads2inspire)
[![PyPI version](https://badge.fury.io/py/ads2inspire.svg)](https://badge.fury.io/py/ads2inspire)
[![DOI](https://zenodo.org/badge/273416634.svg)](https://zenodo.org/badge/latestdoi/273416634)
[![Conda Version](https://img.shields.io/conda/vn/conda-forge/ads2inspire.svg)](https://anaconda.org/conda-forge/ads2inspire)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/duetosymmetry/ads2inspire/blob/master/LICENSE)

# ads2inspire
Replace ADS citations with the appropriate INSPIRE ones in latex and bibtex

Why? Because ADS citation keys are not stable: they start out as something like `2019arXiv191207609s`,
and after being accepted to a journal turn into something like `2020PhRvD.101f4007S`. This means you
have to rewrite your latex, or you might even end up citing both entries!

## Installation

### From PyPI

In your Python environment run

```
python -m pip install ads2inspire
```

### From conda-forge

In your conda environment run

```
conda install -c conda-forge ads2inspire
```

### From this repository

In your Python environment from the top level of this repository run

```
python -m pip install .
```

### From GitHub

In your Python environment run

```
python -m pip install "git+https://github.com/duetosymmetry/ads2inspire.git#egg=ads2inspire"
```

## Usage
First latex/bibtex/latex your file, then run

```shell
ads2inspire [--backup] [--filter-type [ads|all]] auxfile.aux [texfile1.tex [texfile2.tex [...]]]
```

If your main tex file is named `wonderful.tex`, then your auxfile will be named `wonderful.aux`.
`ads2inspire` will read the aux file, query INSPIRE, then rewrite all the texfiles named on the
command line, and append to the first bibtex file named in auxfile.  The option `--backup` will
make the program write backups of the tex and bib files before rewriting them.  The option
`--filter-type` controls which keys to search for on INSPIRE: the default `"ads"` will only
search for keys that look like ADS keys, while `"all"` will try all keys (aside from those that
look like INSPIRE keys).

## Contributing

Note that I have done very little testing! Want to pitch in and help make this code better?
Please fork and send me PRs!

TODO:
- More testing
- More filter types
- more?
