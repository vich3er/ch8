# Результат 2. SPARQL-запити до компетентнісних питань

Артефакти: queries/q1_select.rq ... queries/q8_federated.rq, docs/sparql_results.md.
Запити виконано скриптом scripts/querry_runner.py над графом data/kb.ttl (397 триплетів). У всіх запитах оголошено PREFIX : <http://www.semanticweb.org/patient_monitoring#>.

## Запит 1. SELECT

Питання (CQ): які медичні пристрої моніторингу закріплені за пацієнтами?

```sparql
SELECT ?patient ?device WHERE {
    ?patient :isMonitoredBy ?device .
}
```

Результат: 31 рядок, наприклад (:patient_04, :dev_device_04), (:patient_05, :dev_device_05).
Інтерпретація: кожен із 29 згенерованих пацієнтів пов'язаний зі своїм пристроєм, ще два зв'язки походять з даних ЛР 7. Зв'язки моніторингу в онтології наявні.

## Запит 2. ASK

Питання (CQ): чи наявні в системі зареєстровані гострі стани (AcuteCondition)?

```sparql
ASK WHERE { ?condition a :AcuteCondition . }
```

Результат: False.
Інтерпретація: клас :AcuteCondition оголошено в онтології, але екземплярів у графі немає. Єдиний стан у даних, :cond_heart_failure, має тип :ChronicCondition.

## Запит 3. CONSTRUCT

Питання (CQ): як побудувати прямий зв'язок від пацієнта до його відгуків?

```sparql
CONSTRUCT { ?patient :hasFeedback ?feedback . }
WHERE     { ?feedback :submittedBy ?patient . }
```

Результат: граф із трьох триплетів: (:patient_01 :hasFeedback :fb_01), (:patient_02 :hasFeedback :fb_02), (:patient_03 :hasFeedback :fb_03).
Інтерпретація: запит інвертує відношення :submittedBy й будує прямий зв'язок від пацієнта до відгуку.

## Запит 4. Агрегація

Питання (CQ): яка загальна кількість поданих відгуків усіх типів?

```sparql
SELECT (COUNT(?feedback) AS ?totalFeedback) WHERE {
    { ?feedback a :PatientFeedback . }
    UNION
    { ?feedback a :SymptomFeedback . }
    UNION
    { ?feedback a :ServiceFeedback . }
}
```

Результат: totalFeedback = 3.
Інтерпретація: у графі три відгуки: fb_01 і fb_03 типу :SymptomFeedback та fb_02 типу :ServiceFeedback. Конструкція UNION охоплює всі підкласи відгуків, оскільки rdflib не виконує RDFS-виведення.

## Запит 5. OPTIONAL

Питання (CQ): які текстові відгуки залишили пацієнти, з урахуванням тих, хто відгуків не залишав?

```sparql
SELECT ?patient ?text WHERE {
    ?patient a :Patient .
    OPTIONAL { ?feedback :submittedBy ?patient ; :hasFeedbackText ?text . }
}
```

Результат: 29 рядків, по одному на кожного пацієнта. Текст відгуку мають :patient_01 («Задишка посилилась під час ходьби») і :patient_02 («Чудовий догляд медсестри у палаті»), в інших змінна ?text не зв'язана.
Інтерпретація: OPTIONAL зберігає в результаті пацієнтів без текстових відгуків.

## Запит 6. FILTER

Питання (CQ): які виміряні показники життєдіяльності перевищують порогове значення 100.0?

```sparql
SELECT ?vitalSign ?value WHERE {
    ?vitalSign :hasValueNumeric ?value .
    FILTER (?value > 100.0)
}
```

Результат: 30 рядків зі значеннями від 121.0 до 149.0, наприклад (:vital_sign_29, 149.0), (:vital_hr_01, 125.0).
Інтерпретація: з 31 показника поріг перевищують 30; показник :vital_spo2_01 зі значенням 88.5 у вибірку не потрапляє.

## Запит 7. Property path

Питання (CQ): які симптоми пов'язані між собою через один або декілька проміжних зв'язків?

```sparql
SELECT ?symptom1 ?symptom2 WHERE {
    ?symptom1 :associatedWithSymptom+ ?symptom2 .
}
```

Результат: один рядок (:cond_heart_failure, :symptom_dyspnea).
Інтерпретація: оператор + виконує обхід транзитивного замикання властивості :associatedWithSymptom (довжина шляху одна або більше зв'язків).

## Запит 8. Federated-запит до Wikidata

Питання (CQ): як з'єднати локальні дані із зовнішньою базою знань Wikidata (клас Human)?

```sparql
PREFIX wd:  <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT ?patient ?wdHuman WHERE {
    ?patient a :Patient .
    SERVICE <https://query.wikidata.org/sparql> {
        SELECT ?wdHuman WHERE { ?wdHuman wdt:P31 wd:Q5 . } LIMIT 3
    }
} LIMIT 3
```

Результат: сутності Wikidata wd:Q835, wd:Q838, wd:Q839.
Інтерпретація: блок SERVICE звертається до віддаленого SPARQL-ендпоінта Wikidata й повертає екземпляри класу Human (wd:Q5) разом із локальними пацієнтами.

## Крок 3. Оптимізація повільного запиту

Для порівняння взято запит 6. Неоптимізований варіант використовує невизначений предикат ?p, через що рушій переглядає всі триплети графа, а числовий тип перевіряється функцією isNumeric:

```sparql
SELECT ?vitalSign ?value WHERE {
    ?vitalSign ?p ?value .
    FILTER (isNumeric(?value) && ?value > 100.0)
}
```

Оптимізований варіант (файл q6_filter.rq) указує конкретний предикат :hasValueNumeric, що звужує пошук до 31 триплета ще до застосування фільтра.

Вимірювання виконано за допомогою time.perf_counter на 10 повторах (граф завантажено заздалегідь). Обидва запити повертають однакові 30 рядків.

- Неоптимізований запит: медіана 0.0331 с, мінімум 0.0327 с.
- Оптимізований запит: медіана 0.0063 с, мінімум 0.0061 с.
- Прискорення приблизно в 5.2 раза.

## Крок 4. Ручна перевірка результатів

Результати порівняно з вмістом data/kb.ttl за незалежним підрахунком без SPARQL.

- Запит 1: у файлі 31 триплет :isMonitoredBy, зокрема :patient_04 :isMonitoredBy :dev_device_04. Збігається.
- Запит 4: у файлі три екземпляри відгуків (fb_01, fb_02, fb_03). Збігається з totalFeedback = 3.
- Запит 5: текст відгуку є лише у fb_01 та fb_02. Збігається.
- Запит 6: з 31 значення :hasValueNumeric 30 перевищують 100.0, найменше 121.0, найбільше 149.0. Збігається.
- Запит 7: у файлі єдиний триплет :cond_heart_failure :associatedWithSymptom :symptom_dyspnea. Збігається.

## Висновок

Складено 8 запитів, що охоплюють SELECT, ASK, CONSTRUCT, агрегацію, OPTIONAL, FILTER, property path та federated-запит. Кожен запит пов'язаний з компетентнісним питанням і має інтерпретацію. Оптимізація запиту 6 дала приблизно п'ятикратне прискорення, п'ять запитів перевірено вручну.
