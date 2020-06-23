from pathlib import Path
import re
from time import sleep
import urllib.request
import bibtexparser


def parse_aux(aux_path):
    """Read a .aux file, parse for paths to bib files, referenced keys

    Parameters
    ----------
    aux_path: `PathLike`
      Path to .aux file

    Returns
    -------
    aux: string
      Contents of the aux file

    bib_path_strs: array of string
      An array of strings which are the paths of .bib files which were
      referenced in the aux file

    cite_keys: array of string
      An array of keys which were referenced in the aux file
    """

    aux_path = Path(aux_path)

    with aux_path.open("r") as aux_file:
        aux = aux_file.read()

    # Find out which .bib files were used
    try:
        bib_path_strs = re.search("\\\\bibdata\\{(.*?)\\}", aux).group(1).split(",")
    except:
        bib_path_strs = []

    # And which citation keys were used
    cite_pat = re.compile("\\\\bibcite\\{(.*?)\\}")

    pos = 0
    cite_keys = []
    while True:
        match = cite_pat.search(aux, pos)
        if match is not None:
            cite_keys.append(match.group(1))
            pos = match.span()[1]
        else:
            break

    return aux, bib_path_strs, cite_keys


def load_bib_dbs(bib_path_strs):
    """Read a collection of .bib files using `bibtexparser`.

    Parameters
    ----------
    bib_path_strs: array of string
      An array of strings which are the paths of .bib files to attempt
      to open and parse

    Returns
    -------
    bib_paths: array of `PathLike`
      The Path objects for .bib files that were found and successfully
      parsed.

    bib_dbs: array of `bibtexparser.bibdatabase.BibDatabase`
      The corresponding BibDatabase objects, see documentation for
      bibtexparser for details.
    """

    parser = bibtexparser.bparser.BibTexParser(common_strings = True,
                                               ignore_nonstandard_types = False)

    bib_paths = []
    bib_dbs = []
    for path_str in bib_path_strs:
        if Path(path_str).exists():
            try:
                with open(Path(path_str), "r") as bib_file:
                    bib_db = bibtexparser.load(bib_file, parser)
                    bib_paths.append(path_str)
                    bib_dbs.append(bib_db)
            except Exception as e:
                print(f"{path_str} exists but parsing failed, error:")
                print(repr(e))
        elif Path(path_str + ".bib").exists():
            try:
                with open(Path(path_str + ".bib"), "r") as bib_file:
                    bib_db = bibtexparser.load(bib_file, parser)
                    bib_paths.append(path_str + ".bib")
                    bib_dbs.append(bib_db)
            except Exception as e:
                print(f"{path_str} exists but parsing failed, error")
                print(repr(e))
        else:
            print(f"Neither {path_str} nor {path_str}.bib exist")
            pass

    return bib_paths, bib_dbs


def filter_ads_keys(cite_keys):
    """Select keys matching the pattern of ADS bibtex keys.

    The current pattern to match is: `"\d\d\d\d..............."`

    Parameters
    ----------
    cite_keys: array of string
      An array of bibtex keys

    Returns
    -------
    ads_keys: array of string
      The matching keys from cite_keys
    """

    ads_pat = re.compile("\d\d\d\d...............")
    return [key for key in cite_keys if ads_pat.match(key) is not None]


def filter_matchable_fields(cite_keys, bib_dbs, desired_fields=["eprint", "doi"]):
    """Select bibtex entries which have certain desired fields.

    To look up an entry in a different database, we need a
    well-known identifier like a DOI or arXiv identifier.  This
    function will select those entries which have enough info (by
    having desired fields) that we can search for them in another DB.
    The return is a mapping from bibkeys to their bib entries, where
    the entries have been stripped down to only the desired well-known
    identifiers.

    Parameters
    ----------
    cite_keys: array of string
      Bibtex keys to filter

    bib_dbs: array of `bibtexparser.bibdatabase.BibDatabase`

    desired_fields: array of string, optional [default: `['eprint', 'doi']`]
      Fields whose presence lets us search in another DB.

    Returns
    -------
    key_mapping: dict
      For a key `ads_key`, the value is a dict which is a filtered bib
      entry.  This resulting dict has keys coming from
      `desired_fields`.  For example, you can access
      `key_mapping[ads_key]['doi']`.
    """

    key_mapping = {}
    for ads_key in cite_keys:
        for bib_db in bib_dbs:
            if ads_key in bib_db.entries_dict:
                entry = bib_db.entries_dict[ads_key]
                filtered_entry = {
                    field: val for field, val in entry.items() if field in desired_fields
                }
                if len(filtered_entry) > 0:
                    key_mapping[ads_key] = filtered_entry

    return key_mapping


def maybe_get_insp_bib(url, max_retries=3, sleep_ms=500):
    """Try to query an INSPIRE URL, with retries, and sleeping

    Parameters
    ----------
    url: string

    max_retries: int, optional [default: 3]

    sleep_ms: numeric, optional [default: 500]
      Length of sleep (in milliseconds) between HTTP 429 codes

    Returns
    -------
    response: bytes or None
      The positive response from INSPIRE; None if an error occurs, or
      if we failed the max number of times.
    """

    print(f"requesting {url}")
    n_retries = 0
    while n_retries < max_retries:
        try:
            req = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            print(e)
            if e.code == 429:
                retry_time = req.getheaders()["retry-in"]
                print(f'got 429 with "retry-in"={retry_time}')
                print(f"going to sleep for {sleep_ms}ms")
                sleep(sleep_ms / 1000.0)
                n_retries = n_retries + 1
                continue
            else:
                return None
        except urllib.error.URLError as e:
            print(e)
            return None
        else:  # Success
            return req.read()
    # maxed out on retries
    print(f"too many ({n_retries}) retries")
    return None


def maybe_get_insp_bib_methods(possible_keys, max_retries_per_key=3, sleep_ms=500):
    """Try to query INSPIRE using a dictionary of possible keys.

    Currently supported keys are 'doi' and 'eprint'.

    Parameters
    ----------
    possible_keys: dict
      Keys are one of 'doi', 'eprint'.

    max_retries_per_key: int, optional [default: 3]

    sleep_ms: numeric, optional [default: 500]
      Length of sleep (in milliseconds) between HTTP 429 codes

    Returns
    -------
     response: bytes or None
      The positive response from INSPIRE; None if an error occurs, or
      if we failed the max number of times.
    """

    insp_api_base = "https://inspirehep.net/api/"
    fetchers = {
        "doi": (lambda doi: insp_api_base + "doi/" + doi + "?format=bibtex"),
        "eprint": (lambda eprint: insp_api_base + "arxiv/" + eprint + "?format=bibtex"),
    }

    possible_urls = [fetchers[method](val) for method, val in possible_keys.items()]

    for url in possible_urls:
        bibdata = maybe_get_insp_bib(url, max_retries=max_retries_per_key, sleep_ms=sleep_ms)
        if bibdata is not None:
            return bibdata
        else:
            sleep(sleep_ms / 1000.0)

    # If we got here, failed to find an INSPIRE entry
    return None


def extract_key_from_bib_str(bibdata):
    """Extract the bib key from a single bib entry.

    Parameters
    ----------
    bibdata: string
      A string containing one bibliography entry, e.g. a string that
      starts like "@article{Stein:2019buj,\n".

    Returns
    -------
    key: string
    """

    match = re.match("@(.*?)\\{(.*?),", bibdata)
    if match is not None:
        return match.group(2)
    else:
        return None


def get_insp_replacements_query(key_mapping, max_retries_per_key=3, sleep_ms=500):
    """Query INSPIRE for replacement keys.

    Parameters
    ----------
    key_mapping: dict
      Same format as that returned by `filter_matchable_fields`:
      For a key `ads_key`, the value is a dict which is a filtered bib
      entry.  This resulting dict has keys coming from
      `desired_fields`.  For example, you can access
      `key_mapping[ads_key]['doi']`.

    max_retries_per_key: int, optional [default: 3]

    sleep_ms: numeric, optional [default: 500]
      Length of sleep (in milliseconds) between HTTP 429 codes

    Returns
    -------
    replacements: array of dict
      Each dict has keys "ads_key", "insp_key", and "bib_str".
    """

    replacements = []

    for ads_key, possible_keys in key_mapping.items():
        bibdata = maybe_get_insp_bib_methods(possible_keys,
                                             max_retries_per_key=max_retries_per_key,
                                             sleep_ms=sleep_ms)
        if bibdata is None:
            print(f"No bib entries found for ads_key={ads_key}")
        else:
            bib_str = bibdata.decode("utf-8")
            insp_key = extract_key_from_bib_str(bib_str)
            rep_data = {"ads_key": ads_key, "insp_key": insp_key, "bib_str": bib_str}
            replacements.append(rep_data)

    return replacements


def find_already_present_insp_keys(replacements, bib_dbs):
    """Filter replacements to those whose INSPIRE key appear in bibs.

    Parameters
    ----------
    replacements: array of dict
      Each dict has keys "ads_key", "insp_key", and "bib_str".

    bib_dbs: array of `bibtexparser.bibdatabase.BibDatabase`

    Returns
    -------
    already_present_insp_keys: set of string
      Strings are INSPIRE keys appearing in `bib_dbs`
    """

    already_present_insp_keys = []
    for rep in replacements:
        for bib_db in bib_dbs:
            if rep["insp_key"] in bib_db.entries_dict:
                already_present_insp_keys.append(rep["insp_key"])

    return set(already_present_insp_keys)


def rewrite_tex_file(texpath, replacements, backup=False):
    """Rewrite a tex file, replacing ADS keys with INSPIRE keys.

    Parameters
    ----------
    texpath: PathLike
      Path to tex file to rewrite

    replacements: array of dict
      Each dict has keys "ads_key", "insp_key", and "bib_str".

    backup: bool, optional [default: False]
      If True, first back up the tex file (using suffix ".bak.tex")
    """

    texpath = Path(texpath)

    with texpath.open("r") as texfile:
        tex = texfile.read()

    if backup:
        with texpath.with_suffix(".bak.tex").open("w") as backupfile:
            backupfile.write(tex)

    for rep in replacements:
        tex = tex.replace(rep["ads_key"], rep["insp_key"])

    with texpath.open("w") as texfile:
        texfile.write(tex)


def append_needed_to_bib_file(bibpath, replacements, bib_dbs, backup=False):
    """Append needed INSPIRE bib entried to bib file.

    Filters `replacements` down, using `bib_dbs`, to just those which
    are missing; then appends their bib entries to the bib file.

    Parameters
    ----------
    bibpath: PathLike
      Path to bib file to append

    replacements: array of dict
      Dicts mapping ADS keys to INSPIRE keys, with bib entries.
      Each dict has keys "ads_key", "insp_key", and "bib_str".

    bib_dbs: array of `bibtexparser.bibdatabase.BibDatabase`

    backup: bool, optional [default: False]
      If True, first back up the bib file (using suffix ".bak.bib")

    """

    bibpath = Path(bibpath)

    all_fetched_insp_keys = {rep["insp_key"] for rep in replacements}
    already_present_insp_keys = find_already_present_insp_keys(replacements, bib_dbs)
    need_to_write_insp_keys = all_fetched_insp_keys - already_present_insp_keys

    if len(need_to_write_insp_keys) == 0:
        return

    if bibpath.exists():
        pass
    elif bibpath.with_suffix(".bib").exists():
        bibpath = bibpath.with_suffix(".bib")
    else:
        print(f"Neither {bibpath} nor {bibpath}.bib exists")
        raise FileExistsError

    with bibpath.open("r") as bibfile:
        bib = bibfile.read()

    if backup:
        with bibpath.with_suffix(".bak.bib").open("w") as backupfile:
            backupfile.write(bib)

    breaker = "%" * 60 + "\n"
    bib = bib + "\n" + breaker + breaker + "\n"

    for rep in replacements:
        if rep["insp_key"] in need_to_write_insp_keys:
            bib = bib + rep["bib_str"] + "\n"

    with bibpath.open("w") as bibfile:
        bibfile.write(bib)
