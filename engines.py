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
    IdentifiableEntity, BibliographicEntity, Citation,
    AuthorSelfCitation, JournalSelfCitation,
)
from query_handlers import BibliographicEntityQueryHandler, CitationQueryHandler

def _row_to_bib_entity(row) -> BibliographicEntity:
    authors = [a.strip() for a in str(row.get("author", "")).split(";") if a.strip()]
    return BibliographicEntity(
        id               = [row.get("internalId", "unknown")],
        title            = str(row.get("title", "")),
        author           = authors,
        publication_date = str(row.get("pub_date", "")),
        venue            = str(row.get("venue", "")),
    )


def _choose_cls(row) -> type:
    is_asc = str(row.get("author_sc",  "")).strip().lower() == "yes"
    is_jsc = str(row.get("journal_sc", "")).strip().lower() == "yes"
    if is_asc:
        return AuthorSelfCitation
    if is_jsc:
        return JournalSelfCitation
    return Citation


def _row_to_citation(row, entity_map: dict, forced_cls=None) -> Citation:
    cls       = forced_cls if forced_cls is not None else _choose_cls(row)
    oci       = str(row.get("oci", "unknown"))
    citing_id = str(row.get("citing", ""))
    cited_id  = str(row.get("cited",  ""))
    return cls(
        id            = [oci],
        creation      = str(row.get("creation", "")),
        timespan      = str(row.get("timespan", "")),
        citing_entity = entity_map.get(citing_id,
                            BibliographicEntity(id=[citing_id or "unknown"])),
        cited_entity  = entity_map.get(cited_id,
                            BibliographicEntity(id=[cited_id  or "unknown"])),
    )

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

    def getEntityById(self, id: str) -> IdentifiableEntity:
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

    def getCitationsWithinTimespan(self, min_ts: str = None, max_ts: str = None) -> list:
        return self._to_citations(
            self._merge_cit([h.getCitationsWithinTimespan(min_ts, max_ts)
                             for h in self.citationQuery]))

    def getCitationsWithinDate(self, start: str = None, end: str = None) -> list:
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

    def getBibliographicEntitiesWithinDate(
            self, start: str = None, end: str = None) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getBibliographicEntitiesWithinPublicationDate(start, end)
                             for h in self.bibliographicEntityQuery]))

    def getBibliographicEntitiesWithinPublicationDate(
            self, start: str = None, end: str = None) -> list:
        return self.getBibliographicEntitiesWithinDate(start, end)

    def getBibliographicEntitiesWithVenue(self, venue: str) -> list:
        return self._to_bib_entities(
            self._merge_bib([h.getBibliographicEntitiesWithVenue(venue)
                             for h in self.bibliographicEntityQuery]))

class FullQueryEngine(BasicQueryEngine):
    def getAuthorSelfCitationsByName(self, author_name: str) -> list:
        nl = author_name.lower()
        return [c for c in self.getAllAuthorSelfCitations()
                if any(nl in a.lower() for a in c.getCitingEntity().getAuthors())
                and any(nl in a.lower() for a in c.getCitedEntity().getAuthors())]

    def getJournalSelfCitationsByName(self, journal_name: str) -> list:
        nl = journal_name.lower()
        return [c for c in self.getAllJournalSelfCitations()
                if nl in c.getCitingEntity().getVenue().lower()
                and nl in c.getCitedEntity().getVenue().lower()]
    
    def getCitationsOfBibEntityByTitleWithinDate(
            self, bib_entity_title: str, min_date: str, max_date: str) -> list:
        ids: set = set()
        for ent in self.getBibliographicEntitiesWithTitle(bib_entity_title):
            ids.update(ent.getIds())
        if not ids:
            return []
        return [c for c in self.getCitationsWithinDate(min_date, max_date)
                if set(c.getCitedEntity().getIds()) & ids]

    def getReferencesOfBibEntityByTitleWithinTimespan(
            self, bib_entity_title: str, min_timespan: str, max_timespan: str) -> list:
        ids: set = set()
        for ent in self.getBibliographicEntitiesWithTitle(bib_entity_title):
            ids.update(ent.getIds())
        if not ids:
            return []
        return [c for c in self.getCitationsWithinTimespan(min_timespan, max_timespan)
                if set(c.getCitingEntity().getIds()) & ids]    