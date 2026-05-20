import subprocess
import sys

for _pkg in ["pandas"]:
    try:
        __import__(_pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pkg, "-q"])

from sqlite3 import connect
from pandas import DataFrame, read_sql, concat

from model import (
    BibliographicEntity, Citation,
    AuthorSelfCitation, JournalSelfCitation,
)
from query_handlers import BibliographicEntityQueryHandler, CitationQueryHandler

class BasicQueryEngine:
    def __init__(self):
        self.citationQuery:            list = []
        self.bibliographicEntityQuery: list = []

    def cleanCitationHandlers(self) -> bool:
        self.citationQuery = []
        return True

    def cleanBibliographicEntityHandlers(self) -> bool:
        self.bibliographicEntityQuery = []
        return True

    def addCitationHandler(self, handler: CitationQueryHandler) -> bool:
        self.citationQuery.append(handler)
        return True

    def addBibliographicEntityHandler(self, handler: BibliographicEntityQueryHandler) -> bool:
        self.bibliographicEntityQuery.append(handler)
        return True

    def _entity_map(self) -> dict:
        em = {}
        for h in self.bibliographicEntityQuery:
            with connect(h.dbPathOrUrl) as con:
                df_bib = read_sql("SELECT * FROM BibliographicEntity", con)
                df_ids = read_sql("SELECT * FROM EntityId", con)
            for _, row in df_bib.iterrows():
                ent = _row_to_bib_entity(row)
                em[row["internalId"]] = ent
            for _, row in df_ids.iterrows():
                ent = em.get(row["internalId"])
                if ent is not None:
                    em[row["id"]] = ent
        return em

    def _merge_bib(self, dfs: list) -> DataFrame:
        if not dfs:
            return DataFrame()
        return concat(dfs, ignore_index=True).drop_duplicates(subset=["internalId"])

    def _merge_cit(self, dfs: list) -> DataFrame:
        non_empty = [d for d in dfs if not d.empty]
        if not non_empty:
            return DataFrame()
        return concat(non_empty, ignore_index=True).drop_duplicates(subset=["oci"])

    def _to_citations(self, df: DataFrame, forced_cls=None) -> list:
        if df.empty:
            return []
        em = self._entity_map()
        return [_row_to_citation(row, em, forced_cls) for _, row in df.iterrows()]

    def _to_bib_entities(self, df: DataFrame) -> list:
        return [_row_to_bib_entity(row) for _, row in df.iterrows()]

    def getEntityById(self, id: str):
        for h in self.bibliographicEntityQuery:
            df = h.getById(id)
            if not df.empty:
                return _row_to_bib_entity(df.iloc[0])
        for h in self.citationQuery:
            df = h.getById(id)
            if not df.empty:
                return _row_to_citation(df.iloc[0], self._entity_map())
        return None

    def getAllCitations(self) -> list:
        return self._to_citations(
            self._merge_cit([h.getAllCitations() for h in self.citationQuery]))

    def getAllAuthorSelfCitations(self) -> list:
        return self._to_citations(
            self._merge_cit([h.getAllAuthorSelfCitations() for h in self.citationQuery]),
            forced_cls=AuthorSelfCitation)

    def getAllJournalSelfCitations(self) -> list:
        return self._to_citations(
            self._merge_cit([h.getAllJournalSelfCitations() for h in self.citationQuery]),
            forced_cls=JournalSelfCitation)

    def getCitationsWithinTimespan(self, min_ts: str, max_ts: str) -> list:
        return self._to_citations(
            self._merge_cit([h.getCitationsWithinTimespan(min_ts, max_ts)
                             for h in self.citationQuery]))

    def getCitationsWithinDate(self, start: str, end: str) -> list:
        return self._to_citations(
            self._merge_cit([h.getCitationsWithinDate(start, end)
                             for h in self.citationQuery]))

    def getAllBibliographicEntities(self) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getAllBibliographicEntities()
                             for h in self.bibliographicEntityQuery]))

    def getBibliographicEntitiesWithTitle(self, title: str) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getBibliographicEntitiesWithTitle(title)
                             for h in self.bibliographicEntityQuery]))

    def getBibliographicEntitiesWithAuthor(self, author: str) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getBibliographicEntitiesWithAuthor(author)
                             for h in self.bibliographicEntityQuery]))

    def getBibliographicEntitiesWithinPublicationDate(
            self, start: str, end: str) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getBibliographicEntitiesWithinPublicationDate(start, end)
                             for h in self.bibliographicEntityQuery]))

    def getBibliographicEntitiesWithVenue(self, venue: str) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getBibliographicEntitiesWithVenue(venue)
                             for h in self.bibliographicEntityQuery]))
