from pathlib import Path
import argparse
import re
from time import sleep
import urllib.request
import bibtexparser


def parse_aux(aux_path):
    """TODO Documentation"""

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
    """TODO Documentation"""

    bib_paths = []
    bib_dbs = []
    for path_str in bib_path_strs:
        if Path(path_str).exists():
            try:
                with open(Path(path_str), "r") as bib_file:
                    bib_db = bibtexparser.load(bib_file)
                    bib_paths.append(path_str)
                    bib_dbs.append(bib_db)
            except Exception as e:
                print("{} exists but parsing failed, error:".format(path_str))
                print(repr(e))
        elif Path(path_str + ".bib").exists():
            try:
                with open(Path(path_str + ".bib"), "r") as bib_file:
                    bib_db = bibtexparser.load(bib_file)
                    bib_paths.append(path_str + ".bib")
                    bib_dbs.append(bib_db)
            except Exception as e:
                print("{} exists but parsing failed, error".format(path_str))
                print(repr(e))
        else:
            print("Neither {} nor {}.bib exist".format(path_str, path_str))
            pass

    return bib_paths, bib_dbs


def filter_ads_keys(cite_keys):
    """TODO Documentation"""

    ads_pat = re.compile("\d\d\d\d...............")
    return [key for key in cite_keys if ads_pat.match(key) is not None]


def filter_matchable_keys(cite_keys, bib_dbs, desired_keys=["eprint", "doi"]):
    """TODO Documentation"""

    key_mapping = {}
    for ads_key in cite_keys:
        for bib_db in bib_dbs:
            if ads_key in bib_db.entries_dict:
                entry = bib_db.entries_dict[ads_key]
                filtered_entry = {
                    key: val for key, val in entry.items() if key in desired_keys
                }
                if len(filtered_entry) > 0:
                    key_mapping[ads_key] = filtered_entry

    return key_mapping


def maybe_get_insp_bib(url, max_retries=3, sleep_ms=500):

    print("requesting {}".format(url))
    n_retries = 0
    while n_retries < max_retries:
        try:
            req = urllib.request.urlopen(url)
        except urllib.error.HTTPError as e:
            print(e)
            if e.code == 429:
                retry_time = req.getheaders()["retry-in"]
                print('got 429 with "retry-in"={}'.format(retry_time))
                print("going to sleep for {}ms".format(sleep_ms))
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
    print("too many ({}) retries".format(n_retries))
    return None


def maybe_get_insp_bib_methods(ads_key, other_keys, sleep_ms=500):
    """TODO document this.
    ads_key is a string.
    other_keys is a dict where keys are in
    `desired_keys` and vals are the new paper keys"""

    insp_api_base = "https://inspirehep.net/api/"
    fetchers = {
        "doi": (lambda doi: insp_api_base + "doi/" + doi + "?format=bibtex"),
        "eprint": (lambda eprint: insp_api_base + "arxiv/" + eprint + "?format=bibtex"),
    }

    possible_urls = [fetchers[method](val) for method, val in other_keys.items()]

    for url in possible_urls:
        bibdata = maybe_get_insp_bib(url, sleep_ms=sleep_ms)
        if bibdata is not None:
            return bibdata
        else:
            sleep(sleep_ms / 1000.0)
    print("No bib entries found for ads_key={}".format(ads_key))
    return None


def insp_key_from_bib_str(bibdata):
    match = re.match("@(.*?)\\{(.*?),", bibdata)
    if match is not None:
        return match.group(2)
    else:
        return None


def get_insp_replacements_query(key_mapping):
    """TODO Documentation"""

    replacements = []

    for ads_key, other_keys in key_mapping.items():
        bibdata = maybe_get_insp_bib_methods(ads_key, other_keys, sleep_ms=1)
        if bibdata is not None:
            bib_str = bibdata.decode("utf-8")
            insp_key = insp_key_from_bib_str(bib_str)
            rep_data = {"ads_key": ads_key, "insp_key": insp_key, "bib_str": bib_str}
            replacements.append(rep_data)

    return replacements


def find_already_present_insp_keys(replacements, bib_dbs):
    """TODO Documentation"""

    already_present_insp_keys = []
    for rep in replacements:
        for bib_db in bib_dbs:
            if rep["insp_key"] in bib_db.entries_dict:
                already_present_insp_keys.append(rep["insp_key"])

    return set(already_present_insp_keys)


def rewrite_tex_file(texpath, replacements, backup=False):
    """TODO Documentation"""

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


def appended_needed_to_bib_file(bibpath, replacements, bib_dbs, backup=False):
    """TODO Documentation"""

    bibpath = Path(bibpath)

    all_fetched_insp_keys = {rep["insp_key"] for rep in replacements}
    already_present_insp_keys = find_already_present_insp_keys(replacements, bib_dbs)
    need_to_write_insp_keys = all_fetched_insp_keys - already_present_insp_keys

    if bibpath.exists():
        pass
    elif bibpath.with_suffix(".bib").exists():
        bibpath = bibpath.with_suffix(".bib")
    else:
        print("Neither {1} nor {1}.bib exists".format(bibpath))
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
