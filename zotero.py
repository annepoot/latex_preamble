from pyzotero import zotero
import unicodedata
import pprint

library_id = "13025343"
library_type = "user"
api_key = "fUQJ8SdchuUoiCEEjLRK9RdU"
output_path = "library.bib"

unused_field_list = [
    "ID",
    "edition",
    "copyright",
    "abstract",
    "urldate",
    "pmid",
    "note",
    "keywords",
]
used_field_list = [
    "address",
    "series",
    # "edition",
    "title",
    "volume",
    # "copyright",
    "isbn",
    "issn",
    "shorttitle",
    "url",
    "doi",
    # "abstract",
    "language",
    "number",
    # "urldate",
    "journal",
    "booktitle",
    "publisher",
    "school",
    "author",
    "editor",
    "day",
    "month",
    "year",
    # "pmid",
    # "note",
    # "keywords",
    "pages",
    # "file",
]


def generate_citation_key(entry, title_len):
    key = ""

    author = entry.get("author", "noauthor")
    first_author = author.split(" and ")[0]
    last_name = first_author.split(", ")[0]
    nfkd = unicodedata.normalize("NFKD", last_name.lower())
    sanitized = "".join(c for c in nfkd if not unicodedata.combining(c))
    sanitized = "".join(c for c in sanitized if c.isalpha() or c in [" ", "-"])
    words = sanitized.split(" ")
    sanitized = [w for w in words if w not in ["-", ""]]
    key += "-".join(sanitized)

    title = entry.get("title", "notitle")
    nfkd = unicodedata.normalize("NFKD", title.lower())
    sanitized = "".join(c for c in nfkd if not unicodedata.combining(c))
    sanitized = "".join(c for c in sanitized if c.isalpha() or c in [" ", "-"])
    words = sanitized.split(" ")
    important_words = [w for w in words if w not in ["a", "an", "the", "on", "-", ""]]
    key += "_" + "-".join(important_words[:title_len])

    year = entry.get("year", "noyear")
    if year != "noyear":
        assert 1500 <= int(year) <= 2100
    key += "_" + year

    return key


def add_entry_to_dict(entries_dict, entry, title_len):
    key = generate_citation_key(entry, title_len)

    if key in entries_dict:
        print(f"key {key} already exists in dict!")
        existing_entry = entries_dict.pop(key)
        renewed_key = add_entry_to_dict(entries_dict, existing_entry, title_len + 1)
        key = add_entry_to_dict(entries_dict, entry, title_len + 1)
        print("\tnew first key:", renewed_key)
        print("\tnew second key:", key)
    else:
        entries_dict[key] = entry

    return key


print(f"Connecting to Zotero with ID {library_id} and API key {api_key}")
zot = zotero.Zotero(library_id=library_id, library_type=library_type, api_key=api_key)

print("Collecting all Zotero entries through API")
entries = zot.everything(zot.items(format="bibtex")).entries

print("Creating dict with unique citation keys")
entries_dict = {}

for entry in entries:
    key = add_entry_to_dict(entries_dict, entry, 1)

print("Sorting entries based on citation key")
entries_dict = dict(sorted(entries_dict.items(), key=lambda x: x[0].lower()))

print("Used fields:")
pprint.pp(used_field_list)

print("Unused fields:")
pprint.pp(unused_field_list)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("% Auto-generated with zotero.py\n")
    f.write("% Do not update manually!\n\n")

    for key, value_dict in entries_dict.items():
        item_type = value_dict.pop("ENTRYTYPE")
        f.write("@" + item_type + "{" + key + ",\n")

        url = value_dict.get("url", "")
        doi = value_dict.get("doi", "")

        if len(url) > 0:
            if len(doi) > 0:
                value_dict.pop("url")
            else:
                if "doi.org" in url:
                    doi = url.split("doi.org/")[-1]
                    value_dict["doi"] = doi
                    value_dict.pop("url")

        for field in used_field_list:
            if field in value_dict:
                value = value_dict.pop(field)
                f.write("  " + field + " = {" + value + "},\n")

                if field == "title":
                    if (
                        value
                        == "Probabilistic numerics and uncertainty in computations"
                    ):
                        pass

        for field in unused_field_list:
            if field in value_dict:
                value_dict.pop(field)

        if len(value_dict) > 0:
            for field in value_dict.keys():
                print("unknown field type:", field)

        f.write("}\n\n")

print(f"Written {len(entries_dict)} entries to {output_path}")
