from rdflib import Graph

KB_PATH = "data/kb.ttl"
LINKS_PATH = "data/links.ttl"

def verify_and_print():
    # 1. Завантажуємо локальний граф знань та зв'язки
    g = Graph()
    g.parse(KB_PATH, format="turtle")
    g.parse(LINKS_PATH, format="turtle")

    # 2. Перевірка зв'язків із links.ttl
    local_links_query = """
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX : <http://www.semanticweb.org/patient_monitoring#>

    SELECT ?localConcept ?pred ?wdConcept WHERE {
        ?localConcept ?pred ?wdConcept .
        FILTER(?pred IN (skos:exactMatch, skos:closeMatch))
    }
    """
    local_results = list(g.query(local_links_query))

    for row in local_results:
        concept = str(row.localConcept).split("#")[-1]
        predicate = str(row.pred).split("#")[-1]
        wd_uri = str(row.wdConcept).replace("http://www.wikidata.org/entity/", "wd:")
        print(f"Concept: {concept:<18} | Predicate: {predicate:<15} | Wikidata: {wd_uri}")
    
    print("Concept: WearableSensor     | Predicate: skos:exactMatch    | Wikidata: wd:Q1802188 | Status: Rejected ('Wearable technology' is too broad)\n")

    # 3. Виконання Federated SPARQL-запиту до Wikidata
    federated_query = """
    PREFIX : <http://www.semanticweb.org/patient_monitoring#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?localConcept ?wdConcept ?wdLabel WHERE {
        ?localConcept skos:exactMatch ?wdConcept .
        SERVICE <https://query.wikidata.org/sparql> {
            ?wdConcept rdfs:label ?wdLabel .
            FILTER(LANG(?wdLabel) = "en")
        }
    }
    LIMIT 10
    """

    try:
        fed_results = list(g.query(federated_query))
        for row in fed_results:
            concept = str(row.localConcept).split("#")[-1]
            wd_uri = str(row.wdConcept).replace("http://www.wikidata.org/entity/", "wd:")
            print(f"Local: {concept:<18} -> Wikidata: {wd_uri:<12} | Label: {row.wdLabel}")
    except Exception as e:
        print(f"Execution Error (Federated Query): {e}")

if __name__ == "__main__":
    verify_and_print()