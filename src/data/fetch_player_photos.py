"""Build a Wikidata-sourced photo URL manifest for every player in wiki_squads.parquet.

Uses one batched SPARQL query per ~80 player names to keep request count low.
Image URLs use the Commons Special:FilePath redirect so the site can lazy-load.
"""

from __future__ import annotations

import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

SPARQL = "https://query.wikidata.org/sparql"
UA = "wc2026-quiniela/0.1 (dxr1491@miami.edu)"
OUT = Path("data/raw/photos/manifest.parquet")
SRC = Path("data/raw/squads/wiki_squads.parquet")

BATCH = 60


def _commons_url(filename: str) -> str:
    fn = filename.replace("http://commons.wikimedia.org/wiki/Special:FilePath/", "")
    fn = urllib.parse.unquote(fn)
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(fn)


def query_batch(names: list[str]) -> dict[str, tuple[str, str]]:
    """Return mapping name -> (wikidata_id, image_url) for matched names."""
    values = " ".join(f'"{n.replace(chr(34), "")}"@en' for n in names)
    q = f"""
    SELECT ?item ?itemLabel ?name ?image WHERE {{
      VALUES ?name {{ {values} }}
      ?item rdfs:label ?name .
      ?item wdt:P106 wd:Q937857 .   # association football player
      OPTIONAL {{ ?item wdt:P18 ?image . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    try:
        r = requests.get(
            SPARQL,
            params={"query": q, "format": "json"},
            headers={"User-Agent": UA, "Accept": "application/sparql-results+json"},
            timeout=60,
        )
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        print(f"  sparql batch failed: {e}")
        return {}
    out: dict[str, tuple[str, str]] = {}
    for b in j.get("results", {}).get("bindings", []):
        name = b["name"]["value"]
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        img = b.get("image", {}).get("value", "")
        if name not in out or img:  # prefer record that has image
            out[name] = (qid, _commons_url(img) if img else "")
    return out


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    squads = pd.read_parquet(SRC)
    keys = squads[["team", "player_name"]].drop_duplicates()
    names = keys["player_name"].dropna().unique().tolist()
    print(f"querying {len(names)} unique players in batches of {BATCH}")
    resolved: dict[str, tuple[str, str]] = {}
    for i in range(0, len(names), BATCH):
        chunk = names[i : i + BATCH]
        got = query_batch(chunk)
        resolved.update(got)
        print(f"  batch {i // BATCH + 1}: matched {len(got)}/{len(chunk)} (cum {len(resolved)})")
        time.sleep(1.5)
    rows = []
    for _, r in keys.iterrows():
        qid, url = resolved.get(r["player_name"], ("", ""))
        rows.append(
            {
                "team": r["team"],
                "player_name": r["player_name"],
                "wikidata_id": qid,
                "image_url": url,
            }
        )
    df = pd.DataFrame(rows)
    df.to_parquet(OUT, index=False)
    print(f"wrote {OUT} ({len(df)} rows, {df['image_url'].astype(bool).sum()} with photos)")
    return OUT


if __name__ == "__main__":
    main()
