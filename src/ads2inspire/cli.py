"""The ads2inspire Command Line Interface."""
import logging
import click
from pathlib import Path

from . import (
    parse_aux,
    filter_ads_keys,
    load_bib_dbs,
    filter_matchable_keys,
    get_insp_replacements_query,
    rewrite_tex_file,
    appended_needed_to_bib_file,
)

logging.basicConfig()
log = logging.getLogger(__name__)


@click.command()
@click.argument(
    "auxpath", default=None,
)
@click.argument("texpath", nargs=-1, type=click.Path(), default=None)
@click.option(
    "--backup",
    "-b",
    help="If passed, .tex files will be backed up with extension .bak.tex before being rewritten, and the .bib file will be backed up with .bak.bib before being written.",
    is_flag=True,
)
def ads2inspire(auxpath, texpath, backup):
    """
    Replace ADS citations with the appropriate INSPIRE ones in latex and bibtex

    AUXPATH is the Path to .aux file (if you compiled wonderful.tex this should be wonderful.aux)

    TEXPATH is the Path to the LaTeX file(s) to rewrite
    """

    if Path(auxpath).exists():
        aux, bib_path_strs, cite_keys = parse_aux(Path(auxpath))
    elif Path(auxpath + ".aux").exists():
        aux, bib_path_strs, cite_keys = parse_aux(Path(auxpath + ".aux"))
    else:
        print(f"Neither {auxpath} nor {auxpath}.aux exist")
        quit()

    ads_keys = filter_ads_keys(cite_keys)
    bib_path_strs, bib_dbs = load_bib_dbs(bib_path_strs)
    key_mapping = filter_matchable_keys(ads_keys, bib_dbs)
    replacements = get_insp_replacements_query(key_mapping)

    for path in texpath:
        print("rewriting {}, backup={}".format(path, backup))
        rewrite_tex_file(path, replacements, backup=backup)

    print("appending to {}".format(bib_path_strs[0]))
    appended_needed_to_bib_file(bib_path_strs[0], replacements, bib_dbs, backup=backup)
