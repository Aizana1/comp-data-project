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

from rdflib import Graph, URIRef, Literal, RDF, Namespace
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

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

class CitationUploadHandler(UploadHandler):

    _C_CITATION   = URIRef(BASE_URL + "Citation")
    _C_JOURNAL_SC = URIRef(BASE_URL + "JournalSelfCitation")
    _C_AUTHOR_SC  = URIRef(BASE_URL + "AuthorSelfCitation")

    _P_OCI        = URIRef(BASE_URL + "oci")
    _P_CREATION   = URIRef(BASE_URL + "creation")
    _P_TIMESPAN   = URIRef(BASE_URL + "timespan")
    _P_CITING     = URIRef(BASE_URL + "hasCitingEntity")
    _P_CITED      = URIRef(BASE_URL + "hasCitedEntity")
    _P_JOURNAL_SC = URIRef(BASE_URL + "isJournalSelfCitation")
    _P_AUTHOR_SC  = URIRef(BASE_URL + "isAuthorSelfCitation")
    _P_HAS_ID     = URIRef(BASE_URL + "hasId")

    _CIT_NS = Namespace(BASE_URL + "citation/")
    _ENT_NS = Namespace(BASE_URL + "entity/")

    def pushDataToDb(self, path: str) -> bool:
        try:
            df = pd.read_csv(path, keep_default_na=False, dtype=str)
            g  = Graph()

            for _, row in df.iterrows():
                oci      = row["oci"].strip()
                is_jsc   = row.get("journal_sc", "").strip().lower() == "yes"
                is_asc   = row.get("author_sc",  "").strip().lower() == "yes"
                creation = row.get("creation",   "").strip()
                timespan = row.get("timespan",   "").strip()
                citing_r = row.get("citing",     "").strip()
                cited_r  = row.get("cited",      "").strip()

                subj = self._CIT_NS[_safe_uri(oci)]

                g.add((subj, RDF.type, self._C_CITATION))
                if is_jsc:
                    g.add((subj, RDF.type, self._C_JOURNAL_SC))
                if is_asc:
                    g.add((subj, RDF.type, self._C_AUTHOR_SC))

                g.add((subj, self._P_OCI,        Literal(oci)))
                g.add((subj, self._P_JOURNAL_SC, Literal("yes" if is_jsc else "no")))
                g.add((subj, self._P_AUTHOR_SC,  Literal("yes" if is_asc else "no")))

                if creation:
                    g.add((subj, self._P_CREATION, Literal(creation)))
                if timespan:
                    g.add((subj, self._P_TIMESPAN, Literal(timespan)))

                if citing_r:
                    cn = self._ENT_NS[_safe_uri(citing_r)]
                    g.add((subj, self._P_CITING, cn))
                    g.add((cn,   self._P_HAS_ID, Literal(citing_r)))

                if cited_r:
                    cd = self._ENT_NS[_safe_uri(cited_r)]
                    g.add((subj, self._P_CITED, cd))
                    g.add((cd,   self._P_HAS_ID, Literal(cited_r)))

            import urllib.request
            turtle_data = g.serialize(format="turtle").encode("utf-8")
            req = urllib.request.Request(
                self.dbPathOrUrl,
                data=turtle_data,
                headers={"Content-Type": "text/turtle;charset=utf-8"},
                method="POST",
            )
            urllib.request.urlopen(req)

            return True

        except Exception as e:
            print(f"[CitationUploadHandler] Error: {e}")
            return False
