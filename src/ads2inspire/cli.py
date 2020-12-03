"""The ads2inspire Command Line Interface."""
import logging
import click
from pathlib import Path

from . import (
    parse_aux,
    filter_ads_keys,
    filter_not_insp_keys,
    load_bib_dbs,
    filter_matchable_fields,
    get_insp_replacements_query,
    rewrite_tex_file,
    append_needed_to_bib_file,
    missing_insp_keys,
    missing_key_dummy_mapping,
)

logging.basicConfig()
log = logging.getLogger(__name__)


filter_map = {"ads": filter_ads_keys, "all": filter_not_insp_keys}

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
@click.option(
    "--filter-type",
    "-f",
    type=click.Choice(list(filter_map.keys()), case_sensitive=False),
    default="ads",
    help="Which keys to filter for converting into INSPIRE"
)
@click.option(
    "--fill-missing",
    "-m",
    help="If passed, INSPIRE-like citation keys that were referenced in the LaTeX source but missing from the .bib file will be searched for and inserted if found.",
    is_flag=True,
)
def ads2inspire(auxpath, texpath, backup, filter_type, fill_missing):
    """
    Replace ADS citations with the appropriate INSPIRE ones in latex and bibtex

    AUXPATH is the Path to .aux file (if you compiled wonderful.tex this should be wonderful.aux)

    TEXPATH is the Path to the LaTeX file(s) to rewrite

    You should first run latex/bibtex/latex/latex on your work before running this script.
    The first .bib file named within AUXPATH will receive the new entries.
    """

    auxpath = Path(auxpath)

    if auxpath.exists():
        pass
    elif auxpath.with_suffix(".aux").exists():
        auxpath = auxpath.with_suffix(".aux")
    else:
        print(f"Neither {auxpath} nor {auxpath}.aux exist")
        quit()

    aux, bib_path_strs, cite_keys = parse_aux(auxpath)

    filter_func = filter_map[filter_type.lower()]

    ads_keys = filter_func(cite_keys)
    bib_path_strs, bib_dbs = load_bib_dbs(bib_path_strs)
    key_mapping = filter_matchable_fields(ads_keys, bib_dbs)
    replacements = get_insp_replacements_query(key_mapping)

    if fill_missing:
        missing = missing_insp_keys(cite_keys, bib_dbs)
        missing_key_map = missing_key_dummy_mapping(missing)
        additions = get_insp_replacements_query(missing_key_map)
        replacements = replacements + additions

    for path in texpath:
        print(f"rewriting {path}, backup={backup}")
        rewrite_tex_file(path, replacements, backup=backup)

    print(f"appending to {bib_path_strs[0]}")
    append_needed_to_bib_file(bib_path_strs[0], replacements, bib_dbs, backup=backup)
