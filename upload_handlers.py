import json
import subprocess
import sys

for _pkg in ["pandas", "rdflib"]:
    try:
        __import__(_pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg, "-q"])

import pandas as pd
from sqlite3 import connect


from handler import UploadHandler

BASE_URL = "https://github.com/comp-data/2025-2026/res/"


def _safe_uri(s: str) -> str:
    return s.replace("/", "_").replace(":", "_").replace(" ", "_")


class BibliographicEntityUploadHandler(UploadHandler):
   
    def pushDataToDb(self, path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            entity_rows, id_rows = [], []

            for item in raw:
                ids  = item.get("id", [])
                omid = next((i for i in ids if i.startswith("omid:")), None)
                if omid is None:
                    continue

                for ext_id in ids:
                    id_rows.append({"internalId": omid, "id": ext_id})

                entity_rows.append({
                    "internalId": omid,
                    "title":      item.get("title", ""),
                    "author":     "; ".join(item.get("author", [])),
                    "pub_date":   item.get("pub_date", ""),
                    "venue":      item.get("venue", "") if item.get("venue") else "",
                })

            with connect(self.dbPathOrUrl) as con:
                pd.DataFrame(entity_rows).to_sql(
                    "BibliographicEntity", con, if_exists="replace", index=False)
                pd.DataFrame(id_rows).to_sql(
                    "EntityId", con, if_exists="replace", index=False)
                con.commit()

            return True

        except Exception as e:
            print(f"[BibliographicEntityUploadHandler] Error: {e}")
            return False


