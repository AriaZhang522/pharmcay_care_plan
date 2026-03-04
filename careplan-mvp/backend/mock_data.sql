-- Mock data for careplan MVP (PostgreSQL)
-- Run in DBeaver: connect to DB → open this file → Execute SQL Script (Ctrl+Enter)
-- 使用顺序: patients → referring_providers → orders → care_plans
--
-- DBeaver 连接（Docker 跑着时）: Host=localhost, Port=5433, Database=careplan, User=careplan, Password=131421Zyy!
-- 或用代码导入: docker compose exec backend python manage.py load_mock_data

-- 若表里已有数据，可先清空再导入（取消下面一行注释）
-- TRUNCATE care_plans, orders, referring_providers, patients RESTART IDENTITY CASCADE;

-- 1. 病人表 patients
INSERT INTO patients (first_name, last_name, mrn, dob, created_at) VALUES
('Maria', 'Garcia', 'MRN-MOCK-001', '1958-03-15', NOW()),
('Robert', 'Kim', 'MRN-MOCK-002', '1972-08-22', NOW()),
('Patricia', 'Johnson', 'MRN-MOCK-003', '1965-11-08', NOW())
ON CONFLICT (mrn) DO UPDATE SET first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, dob = EXCLUDED.dob;

-- 2. 医生表 referring_providers
INSERT INTO referring_providers (name, npi, created_at) VALUES
('Dr. James Chen', '1234567890', NOW()),
('Dr. Sarah Williams', '1987654321', NOW()),
('Dr. David Park', '1122334455', NOW())
ON CONFLICT (npi) DO UPDATE SET name = EXCLUDED.name;

-- 3. 订单表 orders（依赖上面两表的 id，用子查询取 id）
INSERT INTO orders (uuid, patient_id, referring_provider_id, primary_diagnosis, additional_diagnoses, medication_name, medication_history, patient_records, created_at)
SELECT v.uuid, p.id, r.id, v.primary_diagnosis, v.additional_diagnoses, v.medication_name, v.medication_history, v.patient_records, NOW()
FROM (VALUES
  ('a1000001-0001-4000-8000-000000000001'::uuid, 'MRN-MOCK-001', '1234567890', 'I10', '["E11.9","E78.00"]'::jsonb, 'Lisinopril 10 mg daily', '["Amlodipine 5mg (discontinued)","Metformin 500mg BID"]'::jsonb, '68 y/o F with HTN, Type 2 DM, hyperlipidemia. BP 148/92. A1c 7.2%.'),
  ('a1000002-0002-4000-8000-000000000002'::uuid, 'MRN-MOCK-002', '1987654321', 'M06.9', '["M17.11","K21.0"]'::jsonb, 'Adalimumab 40 mg every 2 weeks', '["Methotrexate 15mg weekly","Omeprazole 20mg daily"]'::jsonb, '52 y/o M with rheumatoid arthritis, knee OA, GERD. Starting adalimumab.'),
  ('a1000003-0003-4000-8000-000000000003'::uuid, 'MRN-MOCK-003', '1122334455', 'G20', '["F32.1","G47.33"]'::jsonb, 'Carbidopa-Levodopa 25-100 mg TID', '["Pramipexole 0.25mg TID","Sertraline 50mg daily"]'::jsonb, '59 y/o F with Parkinson disease, depression, insomnia. Off periods reported.')
) AS v(uuid, mrn, npi, primary_diagnosis, additional_diagnoses, medication_name, medication_history, patient_records)
JOIN patients p ON p.mrn = v.mrn
JOIN referring_providers r ON r.npi = v.npi
ON CONFLICT (uuid) DO NOTHING;

-- 4. Care Plan 表 care_plans（每个 order 一条，status=completed）
INSERT INTO care_plans (order_id, status, problem_list, goals, pharmacist_interventions, monitoring_plan, error_message, created_at, updated_at)
SELECT o.id, 'completed',
  '["Uncontrolled hypertension (I10)","Type 2 diabetes (E11.9)","Hyperlipidemia (E78.00)"]'::jsonb,
  '["Achieve BP <140/90 mmHg","Maintain A1c <7%","LDL-C at goal"]'::jsonb,
  '["Medication adherence counseling","Review Metformin timing","Discuss DASH diet"]'::jsonb,
  '["Home BP log weekly","A1c every 3 months","Lipid panel annually"]'::jsonb,
  '', NOW(), NOW()
FROM orders o WHERE o.uuid = 'a1000001-0001-4000-8000-000000000001'::uuid
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO care_plans (order_id, status, problem_list, goals, pharmacist_interventions, monitoring_plan, error_message, created_at, updated_at)
SELECT o.id, 'completed',
  '["Rheumatoid arthritis (M06.9)","Knee OA (M17.11)","GERD (K21.0)"]'::jsonb,
  '["Reduce disease activity","Minimize infection risk","Control GERD"]'::jsonb,
  '["Infection signs education","Injection technique for Adalimumab","PPI timing"]'::jsonb,
  '["CBC, CMP, LFT periodically","Monitor infections","Rheumatology follow-up"]'::jsonb,
  '', NOW(), NOW()
FROM orders o WHERE o.uuid = 'a1000002-0002-4000-8000-000000000002'::uuid
ON CONFLICT (order_id) DO NOTHING;

INSERT INTO care_plans (order_id, status, problem_list, goals, pharmacist_interventions, monitoring_plan, error_message, created_at, updated_at)
SELECT o.id, 'completed',
  '["Parkinson disease (G20)","Depression (F32.1)","Insomnia (G47.33)"]'::jsonb,
  '["Optimize on-time with levodopa","Reduce fall risk","Stable mood and sleep"]'::jsonb,
  '["Levodopa on empty stomach 30-60 min before meals","Drug-disease interactions with Sertraline","Fall risk counseling"]'::jsonb,
  '["Document off-periods and dyskinesia","MDS-UPDRS at neurology","Mood and sleep log"]'::jsonb,
  '', NOW(), NOW()
FROM orders o WHERE o.uuid = 'a1000003-0003-4000-8000-000000000003'::uuid
ON CONFLICT (order_id) DO NOTHING;
