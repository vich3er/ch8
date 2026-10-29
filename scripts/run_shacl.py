import pyshacl
from rdflib import Graph

data_graph = Graph().parse("data/kb.ttl", format="turtle")
shapes_graph = Graph().parse("shapes/shapes.ttl", format="turtle")

conforms, results_graph, results_text = pyshacl.validate(
    data_graph,
    shacl_graph=shapes_graph,
    inference='rdfs',
    abort_on_first=False,
    meta_shacl=False,
    advanced=False,
    js=False,
    debug=False
)

print("Conforms:", conforms)
print(results_text)