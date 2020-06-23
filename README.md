# ads2inspire
Replace ADS citations with the appropriate INSPIRE ones in latex and bibtex

Why? Because ADS citation keys are not stable: they start out as something like `2019arXiv191207609s`,
and after being accepted to a journal turn into something like `2020PhRvD.101f4007S`. This means you
have to rewrite your latex, or you might even end up citing both entries!

## Installation

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
ads2inspire [--backup] auxfile.aux [texfile1.tex [texfile2.tex [...]]]
```

If your main tex file is named `wondeful.tex`, then your auxfile will be named `wonderful.aux`.
`ads2inspire` will read the aux file, query INSPIRE, then rewrite all the texfiles named on the
command line, and append to the first bibtex file named in auxfile.  The option `--backup` will
make the program write backups of the tex and bib files before rewriting them.

## Contributing

Note that I have done very little testing! Want to pitch in and help make this code better?
Please fork and send me PRs!

TODO:
- More testing
- Distribution of package for pip/conda
- more?
