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


