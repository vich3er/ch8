import os
import time
from rdflib import Graph

g = Graph()
g.parse("data/kb.ttl", format="turtle")

num = int(input("Enter the query number (1-8): "))
if num < 1 or num > 8:
    raise ValueError("Invalid number")

query_files = {
    1: "q1_select.rq",
    2: "q2_ask.rq",
    3: "q3_construct.rq",
    4: "q4_aggregate.rq",
    5: "q5_optional.rq",
    6: "q6_filter.rq",
    7: "q7_path.rq",
    8: "q8_federated.rq"
}

filename = query_files[num]
filepath = os.path.join("queries", filename)

query_text = None
for enc in ["utf-8", "utf-8-sig", "utf-16", "latin-1"]:
    try:
        with open(filepath, "r", encoding=enc) as f:
            query_text = f.read()
        break
    except UnicodeDecodeError:
        continue

if query_text is None:
    raise RuntimeError("Could not decode query file with any encoding.")

start_time = time.perf_counter()
results = g.query(query_text)
execution_time = time.perf_counter() - start_time

for row in results:
    print(row)

print(f"Execution time: {execution_time:.6f} seconds")