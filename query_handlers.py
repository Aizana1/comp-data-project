
import subprocess
import sys

for _pkg in ["pandas", "sparql-dataframe"]:
    try:
        __import__(_pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg, "-q"])

from sqlite3 import connect
from pandas import DataFrame, read_sql
from sparql_dataframe import get as sparql_get

from handler import QueryHandler

BASE_URL = "https://github.com/comp-data/2025-2026/res/"

class BibliographicEntityQueryHandler(QueryHandler):
    def _q(self, sql: str, params: tuple = ()) -> DataFrame:
        with connect(self.dbPathOrUrl) as con:
            return read_sql(sql, con, params=params)

    def getById(self, id: str) -> DataFrame:
        return self._q(
            """SELECT b.* FROM BibliographicEntity b
               JOIN EntityId e ON b.internalId = e.internalId
               WHERE e.id = ?""",
            (id,))

    def getAllBibliographicEntities(self) -> DataFrame:
        return self._q("SELECT * FROM BibliographicEntity")

    def getBibliographicEntitiesWithTitle(self, title: str) -> DataFrame:
        return self._q(
            "SELECT * FROM BibliographicEntity WHERE LOWER(title) LIKE LOWER(?)",
            (f"%{title}%",))

    def getBibliographicEntitiesWithAuthor(self, author: str) -> DataFrame:
        return self._q(
            "SELECT * FROM BibliographicEntity WHERE LOWER(author) LIKE LOWER(?)",
            (f"%{author}%",))

    def getBibliographicEntitiesWithinPublicationDate(
            self, start_date: str = None, end_date: str = None) -> DataFrame:
        conditions, params = [], []
        if start_date:
            conditions.append("pub_date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("pub_date <= ?")
            params.append(end_date)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return self._q(f"SELECT * FROM BibliographicEntity {where}", tuple(params))

    def getBibliographicEntitiesWithVenue(self, venue: str) -> DataFrame:
        return self._q(
            "SELECT * FROM BibliographicEntity WHERE LOWER(venue) LIKE LOWER(?)",
            (f"%{venue}%",))
    
class CitationQueryHandler(QueryHandler):
    _PFX = f"""
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX base: <{BASE_URL}>
    """

    _BODY = """
        ?cit rdf:type base:Citation ;
             base:oci ?oci .
        OPTIONAL {{ ?cit base:creation              ?creation   }}
        OPTIONAL {{ ?cit base:timespan              ?timespan   }}
        OPTIONAL {{ ?cit base:isJournalSelfCitation ?journal_sc }}
        OPTIONAL {{ ?cit base:isAuthorSelfCitation  ?author_sc  }}
        OPTIONAL {{ ?cit base:hasCitingEntity ?cn . ?cn base:hasId ?citing }}
        OPTIONAL {{ ?cit base:hasCitedEntity  ?cd . ?cd base:hasId ?cited  }}
    """

    _SELECT = "SELECT ?oci ?creation ?timespan ?citing ?cited ?journal_sc ?author_sc"

    def _get(self, query: str) -> DataFrame:
        try:
            return sparql_get(self.dbPathOrUrl, self._PFX + query, True)
        except Exception as e:
            print(f"[CitationQueryHandler] SPARQL error: {e}")
            return DataFrame()

    def getById(self, id: str) -> DataFrame:
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                FILTER(?oci = "{id}")
            }}""")

    def getAllCitations(self) -> DataFrame:
        return self._get(f"{self._SELECT} WHERE {{ {self._BODY} }}")

    def getAllAuthorSelfCitations(self) -> DataFrame:
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                ?cit rdf:type base:AuthorSelfCitation .
            }}""")

    def getAllJournalSelfCitations(self) -> DataFrame:
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                ?cit rdf:type base:JournalSelfCitation .
            }}""")

    def getCitationsWithinTimespan(
            self, min_timespan: str = None, max_timespan: str = None) -> DataFrame:
        parts = []
        if min_timespan:
            parts.append(f'?timespan >= "{min_timespan}"')
        if max_timespan:
            parts.append(f'?timespan <= "{max_timespan}"')
        filter_clause = f"FILTER({' && '.join(parts)})" if parts else ""
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                {filter_clause}
            }}""")

    def getCitationsWithinDate(
            self, start_date: str = None, end_date: str = None) -> DataFrame:
        parts = []
        if start_date:
            parts.append(f'?creation >= "{start_date}"')
        if end_date:
            parts.append(f'?creation <= "{end_date}"')
        filter_clause = f"FILTER({' && '.join(parts)})" if parts else ""
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                {filter_clause}
            }}""")
