from rdflib import Graph

g = Graph()
g.parse("data/onto.owl", format="turtle")
g.parse("data/onto_data.ttl", format="turtle")
g.serialize(destination="data/kb.ttl", format="turtle")

print("Total triples:", len(g))

sub_g = Graph()
count = 0
for s, p, o in g:
    if count < 20:
        sub_g.add((s, p, o))
        count += 1
    else:
        break
sub_g.serialize(destination="data/kb_sample.jsonld", format="json-ld")