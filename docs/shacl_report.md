Результат 3. SHACL-валідація

Артефакти: shapes/shapes.ttl, shapes/defect_shapes.ttl, scripts/run_shacl.py, docs/shacl_report.md.
Інструмент: pySHACL 0.40.1 з режимом inference='rdfs'. Дані: data/kb.ttl (397 триплетів).

Крок 1. Форми та обмеження

У файлі shapes/shapes.ttl описано 5 форм і 14 обмежень семи типів: sh:datatype, sh:minCount, sh:maxCount, sh:pattern, sh:class, sh:minInclusive, sh:maxInclusive.

Форма :MedicalDeviceShape (клас :MedicalDevice): властивість :hasDeviceID має тип xsd:string, рівно одне значення (minCount 1, maxCount 1) і відповідає регулярному виразу ^[A-Z]+-[A-Z0-9]+-[0-9]+$ або ^[A-Z]+-[0-9]+$.

Форма :PatientFeedbackShape (клас :PatientFeedback): властивість :submittedBy має рівно одне значення класу :Patient.

Форма :PatientShape (клас :Patient): властивість :hasAge має тип xsd:integer у діапазоні від 0 до 120.

Форма :AcuteConditionShape (клас :AcuteCondition): властивість rdfs:label обов'язкова й має тип xsd:string.

Форма :ObservationShape (клас :Observation): властивість :observedValue обов'язкова й має тип xsd:decimal.

Крок 2. Валідний набір і набір із дефектами

Валідний набір: форми з файлу shapes/shapes.ttl та дані data/kb.ttl.

Набір з трьома навмисними дефектами (файл shapes/defect_shapes.ttl):

у формі :MedicalDeviceShape задано регулярний вираз ^MUST_START_WITH_AAA-[0-9]+$, якому не відповідає жоден ідентифікатор пристрою;

у формі :PatientFeedbackShape задано sh:minCount 5 для :submittedBy замість одного автора;

у формі :PatientShape для :hasAge задано тип xsd:boolean замість числа.

Крок 3. Результати pySHACL

Валідний набір:

Conforms: True
Validation Report
Conforms: True


Набір із дефектами:

Conforms: False
Results (34):
  31 порушення PatternConstraintComponent (форма :MedicalDeviceShape, шлях :hasDeviceID)
   3 порушення MinCountConstraintComponent (форма :PatientFeedbackShape, шлях :submittedBy)


Приклад запису:

Constraint Violation in PatternConstraintComponent:
  Severity: sh:Violation
  Focus Node: :dev_device_01
  Value Node: Literal("DEV-ID-001", datatype=xsd:string)
  Result Path: :hasDeviceID
  Message: Value does not match pattern '^MUST_START_WITH_AAA-[0-9]+$'


Для відгуків повідомлення має вигляд «Less than 5 values on :fb_01->:submittedBy» (аналогічно для :fb_02 та :fb_03).

Крок 4. Чому SHACL, а не OWL

OWL працює за припущенням відкритого світу: відсутність даних означає не помилку, а те, що факт поки невідомий. Якщо в онтології сказано, що в пристрою має бути ідентифікатор, а в даних його немає, міркувальник просто припустить, що ідентифікатор існує, але не вказаний. До того ж OWL не припускає унікальності імен, тому два різні IRI можуть бути однією сутністю. Основне призначення OWL — логічний вивід нових фактів та виявлення неузгодженості онтології, а не перевірка якості даних.

SHACL перевіряє поточний стан графа за припущенням замкненого світу й для кожного порушення формує окремий запис із вузлом, шляхом і повідомленням. Тому саме SHACL відповідає за обмеження цілісності: обов'язкові властивості (minCount), кількість значень (maxCount), типи даних (datatype), клас об'єкта (class), числові діапазони (minInclusive, maxInclusive) та формат рядків (pattern). Ці обмеження описують, якими мають бути дані, а не що з них логічно випливає.

Висновок

Описано 5 форм із 14 обмеженнями семи типів. Валідний набір проходить перевірку, а набір із дефектами фіксує 34 порушення. Всі результати та аналіз подано у звіті лабораторної роботи, а різницю між SHACL та OWL обґрунтовано.