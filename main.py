from impl import BibliographicEntityUploadHandler, BibliographicEntityQueryHandler
from impl import CitationUploadHandler, CitationQueryHandler
from impl import FullQueryEngine

rel_path = "relational.db"
be = BibliographicEntityUploadHandler()
be.setDbPathOrUrl(rel_path)
be.pushDataToDb("data/dh_metadata.json")

grp_endpoint = "http://127.0.0.1:9999/blazegraph/sparql"
cit = CitationUploadHandler()
cit.setDbPathOrUrl(grp_endpoint)
cit.pushDataToDb("data/dh_citations.csv")

be_qh = BibliographicEntityQueryHandler()
be_qh.setDbPathOrUrl(rel_path)

cit_qh = CitationQueryHandler()
cit_qh.setDbPathOrUrl(grp_endpoint)

que = FullQueryEngine()
que.addBibliographicEntityHandler(be_qh)
que.addCitationHandler(cit_qh)

result_q1 = que.getAllCitations()
print("All citations:", len(result_q1))

result_q2 = que.getCitationsWithinTimespan("P1Y", "P5Y")
print("Within timespan:", len(result_q2))

result_q3 = que.getBibliographicEntitiesWithTitle("Machine learning")
print("With title:", len(result_q3))