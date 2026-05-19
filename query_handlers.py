
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
            self, start_date: str, end_date: str) -> DataFrame:
        return self._q(
            "SELECT * FROM BibliographicEntity WHERE pub_date >= ? AND pub_date <= ?",
            (start_date, end_date))

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
            self, min_timespan: str, max_timespan: str) -> DataFrame:
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                ?cit base:timespan ?timespan .
                FILTER(?timespan >= "{min_timespan}" && ?timespan <= "{max_timespan}")
            }}""")

    def getCitationsWithinDate(
            self, start_date: str, end_date: str) -> DataFrame:
        return self._get(f"""
            {self._SELECT} WHERE {{
                {self._BODY}
                ?cit base:creation ?creation .
                FILTER(?creation >= "{start_date}" && ?creation <= "{end_date}")
            }}""")
