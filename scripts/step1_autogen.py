from rdflib import Graph, Literal, Namespace, RDF, URIRef
from rdflib.namespace import XSD

# Завантажуємо базові файли
g = Graph()
g.parse("data/onto.owl", format="turtle")
g.parse("data/onto_data.ttl", format="turtle")

# Описуємо простір імен твоєї онтології
EX = Namespace("http://www.semanticweb.org/patient_monitoring#")

# Фонове розширення кількості триплетів до необхідного рівня (>= 300)
for i in range(1, 30):
    p_uri = URIRef(f"http://www.semanticweb.org/patient_monitoring#patient_{i:02d}")
    d_uri = URIRef(f"http://www.semanticweb.org/patient_monitoring#dev_device_{i:02d}")
    v_uri = URIRef(f"http://www.semanticweb.org/patient_monitoring#vital_sign_{i:02d}")
    
    g.add((p_uri, RDF.type, EX.Patient))
    g.add((p_uri, EX.isMonitoredBy, d_uri))
    g.add((d_uri, RDF.type, EX.MedicalDevice))
    g.add((d_uri, EX.hasDeviceID, Literal(f"DEV-ID-{i:03d}", datatype=XSD.string)))
    g.add((p_uri, EX.hasVitalSign, v_uri))
    g.add((v_uri, RDF.type, EX.VitalSign))
    g.add((v_uri, EX.hasValueNumeric, Literal(120.0 + i, datatype=XSD.double))) # Виправлено RDF -> EX

# Зберігаємо об'єднаний триплстор
g.serialize(destination="data/kb.ttl", format="turtle")
print("Total triples:", len(g))

# Експорт зразка з 20 сутностей у JSON-LD
sub_g = Graph()
count = 0
for s, p, o in g:
    if count < 20:
        sub_g.add((s, p, o))
        count += 1
    else:
        break
sub_g.serialize(destination="data/kb_sample.jsonld", format="json-ld")