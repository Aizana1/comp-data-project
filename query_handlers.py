
import subprocess
import sys

for _pkg in ["pandas"]:
    try:
        __import__(_pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg, "-q"])

from sqlite3 import connect
from pandas import DataFrame, read_sql

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
