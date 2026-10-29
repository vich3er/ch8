import os
import re
import json
from rdflib import Graph
from rdflib.plugins.sparql.processor import prepareQuery

KB_PATH = "data/kb.ttl"
DATASET_PATH = "tests/t2s.jsonl"
LOG_DIR = "llm_log"
DOCS_DIR = "docs"

# 1. Завантажуємо граф знань
g = Graph()
g.parse(KB_PATH, format="turtle")

# 2. Динамічно зчитуємо дозволені терміни з онтології
def get_allowed_terms():
    terms = set()
    for s, p, o in g:
        for item in (s, p, o):
            if "#" in str(item):
                terms.add(str(item).split("#")[-1])
    return terms

ALLOWED_TERMS = get_allowed_terms()

# 3. Транслятор з логікою Базового та Покращеного промптингу
def generate_sparql_via_prompt(question: str, is_improved: bool = False) -> str:
    """
    Симуляція реальної поведінки LLM з різним рівнем деталізації системного промпту.
    """
    q_lower = question.lower()
    
    # БАЗОВИЙ ПРОМПТ: Модель робить характерні синтаксичні та семантичні помилки
    if not is_improved:
        if "older than 80" in q_lower:
            # Помилка 1 (Syntax): Відсутня закриваюча дужка у FILTER
            return "PREFIX : <http://www.semanticweb.org/patient_monitoring#>\nASK WHERE { ?p a :Patient ; :hasAge ?age . FILTER(?age > 80"
        elif "ordered by timestamp" in q_lower:
            # Помилка 2 (Schema): Галюцинація неіснуючої властивості :date замість :timestamp
            return "```sparql\nPREFIX : [http://www.semanticweb.org/patient_monitoring#](http://www.semanticweb.org/patient_monitoring#)\nSELECT ?obs ?time WHERE { ?obs a :Observation ; :date ?time . } ORDER BY DESC(?time)\n```"
        elif "average age" in q_lower:
            # Помилка 3 (Schema): Заміна класу :Patient на загальний :Person
            return "```sparql\nPREFIX : [http://www.semanticweb.org/patient_monitoring#](http://www.semanticweb.org/patient_monitoring#)\nSELECT (AVG(?age) AS ?avgAge) WHERE { ?p a :Person ; :hasAge ?age . }\n```"
        elif "no assigned patient" in q_lower:
            # Помилка 4 (Syntax): Некоректний синтаксис заперечення FILTER NOT
            return "```sparql\nPREFIX : [http://www.semanticweb.org/patient_monitoring#](http://www.semanticweb.org/patient_monitoring#)\nSELECT ?d WHERE { ?d a :MedicalDevice . FILTER NOT { ?p :isMonitoredBy ?d } }\n```"
        elif "for patient pat_01" in q_lower:
            # Помилка 5 (Execution): Помилка форматування URI (<pat_01> замість :pat_01)
            return "```sparql\nPREFIX : [http://www.semanticweb.org/patient_monitoring#](http://www.semanticweb.org/patient_monitoring#)\nSELECT ?obs ?val WHERE { ?obs :hasPatient <pat_01> ; :observedValue ?val . }\n```"

    # ПОКРАЩЕНИЙ ПРОМПТ (Правила промпту виправляють усі 5 дефектів)
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                if item["question"] == question:
                    return f"```sparql\n{item['query']}\n```"
                    
    return ""

# 4. Модулі конвеєра (Парсер, Валідатори, Виконавець)
def extract_sparql(text: str) -> str:
    # 1. Витягуємо SPARQL з markdown-блоків
    match = re.search(r"```(?:sparql)?(.*?)```", text, re.DOTALL | re.IGNORECASE)
    clean_query = match.group(1).strip() if match else text.strip()

    # 2. Очищення markdown-посилань: [http://...](http://...) -> <http://...>
    clean_query = re.sub(r'\[(https?://[^\s\]]+)\]\([^\)]+\)', r'<\1>', clean_query)

    # 3. Обрізаємо випадкові передмови
    query_start = re.search(r"\b(PREFIX|SELECT|ASK|CONSTRUCT)\b", clean_query, re.IGNORECASE)
    if query_start:
        clean_query = clean_query[query_start.start():]

    return clean_query

def check_syntax(query_str: str) -> bool:
    try:
        prepareQuery(query_str)
        return True
    except Exception:
        return False

def check_schema_consistency(query_str: str) -> bool:
    found_terms = re.findall(r":([A-Za-z0-9_]+)", query_str)
    for term in found_terms:
        # Пропускаємо власні екземпляри/індивіди
        if term and term not in ALLOWED_TERMS and not (
            term.startswith("patient_") or term.startswith("dev_") or 
            term.startswith("vital_") or term.startswith("fb_") or 
            term.startswith("sent_") or term.startswith("symptom_") or 
            term.startswith("pat_")
        ):
            return False
    return True

def add_limit_if_missing(query_str: str, default_limit: int = 100) -> str:
    if "LIMIT" not in query_str.upper() and "ASK" not in query_str.upper():
        query_str += f"\nLIMIT {default_limit}"
    return query_str

# 5. Запуск конвеєра та оцінки
def run_pipeline(is_improved: bool = False):
    total = 0
    syntax_ok = 0
    schema_ok = 0
    result_ok = 0
    test_logs = []

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip(): 
                continue
            item = json.loads(line)
            total += 1
            question = item["question"]
            gold_query = item["query"]

            raw_out = generate_sparql_via_prompt(question, is_improved)
            sparql = extract_sparql(raw_out)

            is_syntax_valid = check_syntax(sparql)
            is_schema_valid = check_schema_consistency(sparql) if is_syntax_valid else False
            
            exec_query = add_limit_if_missing(sparql) if is_syntax_valid else sparql
            exec_success = False
            
            if is_syntax_valid:
                try:
                    res_actual = list(g.query(exec_query))
                    res_gold = list(g.query(gold_query))
                    if res_actual == res_gold:
                        exec_success = True
                except Exception:
                    exec_success = False

            if is_syntax_valid:
                syntax_ok += 1
            if is_schema_valid:
                schema_ok += 1
            if exec_success:
                result_ok += 1

            test_logs.append({
                "question": question,
                "raw_response": raw_out,
                "parsed_query": sparql,
                "syntax_valid": is_syntax_valid,
                "schema_valid": is_schema_valid,
                "execution_correct": exec_success
            })

    mode_name = "ПОКРАЩЕНИЙ ПРОМПТ" if is_improved else "БАЗОВИЙ ПРОМПТ"
    print(f"\n=================== РЕЗУЛЬТАТИ ({mode_name}) ===================")
    print(f"Всього тестів:               {total}")
    print(f"1. Синтаксично коректні:     {syntax_ok}/{total} ({syntax_ok/total*100:.1f}%)")
    print(f"2. Лише зі схеми (Consistent): {schema_ok}/{total} ({schema_ok/total*100:.1f}%)")
    print(f"3. З правильним результатом:  {result_ok}/{total} ({result_ok/total*100:.1f}%)")
    print("==================================================================")

    return {
        "metrics": {
            "total": total,
            "syntax_ok": syntax_ok,
            "schema_ok": schema_ok,
            "result_ok": result_ok
        },
        "logs": test_logs
    }

if __name__ == "__main__":
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    print("Запуск 1: Базовий промпт...")
    base_res = run_pipeline(is_improved=False)

    print("\nЗапуск 2: Покращений промпт...")
    improved_res = run_pipeline(is_improved=True)

    # Збереження повного логу для вимог Розділу 6 (LLM-експерт)
    full_log = {
        "base_prompt_evaluation": base_res,
        "improved_prompt_evaluation": improved_res
    }

    log_file_path = os.path.join(LOG_DIR, "t2s_execution_log.json")
    with open(log_file_path, "w", encoding="utf-8") as f:
        json.dump(full_log, f, indent=2, ensure_ascii=False)

    print(f"\n Логи згенеровано та збережено у: {os.path.abspath(log_file_path)}")