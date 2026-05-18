class IdentifiableEntity:
    def __init__(self, id: list):
        self.id = list(id)

    def getIds(self) -> list:
        return list(self.id)


class BibliographicEntity(IdentifiableEntity):
    def __init__(self, id: list, title: str = "", author: list = None,
                 publication_date: str = "", venue: str = ""):
        super().__init__(id)
        self.title            = title
        self.author           = list(author) if author else []
        self.publication_date = publication_date
        self.venue            = venue

    def getTitle(self) -> str:
        return self.title

    def getAuthors(self) -> list:
        return list(self.author)

    def getPublicationDate(self) -> str:
        return self.publication_date

    def getVenue(self) -> str:
        return self.venue
    
class Citation(IdentifiableEntity):
    def __init__(self, id: list, creation: str, timespan: str,
                 citing_entity: BibliographicEntity,
                 cited_entity: BibliographicEntity):
        super().__init__(id)
        self.creation      = creation
        self.timespan      = timespan
        self.citing_entity = citing_entity
        self.cited_entity  = cited_entity

    def getCreation(self) -> str:
        return self.creation

    def getTimespan(self) -> str:
        return self.timespan

    def getCitingEntity(self) -> BibliographicEntity:
        return self.citing_entity

    def getCitedEntity(self) -> BibliographicEntity:
        return self.cited_entity


class AuthorSelfCitation(Citation):
    pass


class JournalSelfCitation(Citation):
    pass


