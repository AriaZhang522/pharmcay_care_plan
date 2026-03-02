# Care Plan Auto-Generation System — Design Document

**Project:** CVS Specialty Pharmacy Care Plan Generator  
**Version:** 1.0  
**Date:** 2026-03-01

---

## 1. Background & Problem Statement

### 1.1 原始需求

A specialty pharmacy (CVS) needs to automatically generate care plans based on clinical information found within patient records. Currently, pharmacists spend 20–40 minutes per patient assembling these plans manually. Care plans are required for:

- **Compliance** with regulatory standards
- **Medicare reimbursement**
- **Pharma reporting**

The team is short-staffed and backlogged. The system will be used by **medical assistants and pharmacists**, not patients. After a care plan is generated, it is printed and handed to the patient.

### 1.2 用户群体

| 角色 | 操作 |
|------|------|
| Medical Assistant | 通过 Web 表单录入患者信息，触发生成 |
| Pharmacist | 审阅、下载 Care Plan，导出报告 |
| Patient | 不接触系统，接收打印版 Care Plan |

---

## 2. Care Plan 规格

### 2.1 映射关系

- **一个 Care Plan 对应一个订单（一种药物）**
- 同一患者可存在多个 Care Plan（不同药物）

### 2.2 输出内容（必须包含）

| 章节 | 说明 |
|------|------|
| Problem List | 基于 ICD-10 诊断和患者记录 |
| Goals | 治疗目标 |
| Pharmacist Interventions | 药剂师干预措施 |
| Monitoring Plan | 监测计划（指标、频率） |

---

## 3. 功能需求

| 功能 | 是否必须 | 说明 |
|------|----------|------|
| 患者/订单重复检测 | ✅ 必须 | 不能打乱现有工作流 |
| Care Plan 生成 | ✅ 必须 | 核心价值 |
| Provider 重复检测 | ✅ 必须 | 影响 pharma 报告准确性 |
| 导出报告 | ✅ 必须 | pharma 报告需要 |
| Care Plan 下载 | ✅ 必须 | 用户需要上传到他们的系统 |

---

## 4. 数据模型与输入验证

### 4.1 输入字段

| 字段 | 类型 | 验证规则 |
|------|------|----------|
| Patient First Name | string | 非空，仅字母/连字符 |
| Patient Last Name | string | 非空，仅字母/连字符 |
| Patient MRN | string | 唯一 6 位数字 |
| Patient DOB | date | 合法日期，不超过今天 |
| Referring Provider | string | 非空 |
| Referring Provider NPI | string | 精确 10 位数字（Luhn 校验可选） |
| Primary Diagnosis (ICD-10) | string | 符合 ICD-10 格式（如 `G70.01`） |
| Additional Diagnoses | list[string] | 每条符合 ICD-10 格式 |
| Medication Name | string | 非空 |
| Medication History | list[string] | 可为空 |
| Patient Records | string \| PDF | 至少一种必须提供 |

### 4.2 数据库实体（概要）

```
Patient { id, mrn, first_name, last_name, dob, created_at }
Provider { id, npi, name, created_at }
Order { id, patient_id, provider_id, medication_name, primary_dx, additional_dx[], med_history[], raw_records, created_at }
CarePlan { id, order_id, content_json, pdf_path, created_at }
```



## 5. 重复检测规则

### 5.1 患者/订单去重

| 场景 | 处理方式 | 原因 |
|------|----------|------|
| 同一患者 + 同一药物 + **同一天** | ❌ **ERROR** — 必须阻止提交 | 肯定是重复提交 |
| 同一患者 + 同一药物 + **不同天** | ⚠️ **WARNING** — 可确认后继续 | 可能是续方 |
| MRN 相同 + 名字或 DOB 不同 | ⚠️ **WARNING** — 可确认后继续 | 可能是录入错误 |
| 名字 + DOB 相同 + MRN 不同 | ⚠️ **WARNING** — 可确认后继续 | 可能是同一人 |

### 5.2 Provider 去重

| 场景 | 处理方式 | 原因 |
|------|----------|------|
| NPI 相同 + Provider 名字不同 | ❌ **ERROR** — 必须修正 | NPI 是唯一标识符 |

> Provider 只能在系统中录入一次（以 NPI 为主键）。若 NPI 已存在，则复用已有记录，不允许创建同 NPI 的新 Provider。

---

## 6. Care Plan 生成流程

```
用户提交表单
    ↓
后端表单验证（字段格式）
    ↓
重复检测（患者 / 订单 / Provider）
    ↓
ERROR？→ 返回错误，拦截提交
WARNING？→ 前端弹窗，用户确认
    ↓
保存 Patient / Provider / Order 到数据库
    ↓
调用 LLM API（附带结构化 prompt + 患者记录）
    ↓
解析 LLM 输出 → 生成结构化 CarePlan JSON
    ↓
渲染为可下载文本/PDF
    ↓
存储 CarePlan，返回下载链接
```

### 6.1 LLM Prompt 设计（概要）

**System Prompt：**
```
You are a clinical pharmacist generating a care plan for a specialty pharmacy.
Output a JSON object with keys: problem_list, goals, pharmacist_interventions, monitoring_plan.
Each key maps to a list of strings. Be concise and clinically precise.
```

**User Message：**
```
Patient: {first_name} {last_name}, DOB {dob}
Primary Dx: {primary_dx}
Additional Dx: {additional_dx}
Medication: {medication_name}
Medication History: {medication_history}
Patient Records: {patient_records}
```

---

## 7. 示例数据

### 7.1 输入示例

```
Name: A.B.
MRN: 001234
DOB: 1979-06-08 (Age 46)
Sex: Female
Allergies: None known
Medication: IVIG

Primary Dx: Generalized myasthenia gravis, AChR+ (G70.01)
Secondary Dx: Hypertension (I10), GERD (K21.0)

Home Meds:
- Pyridostigmine 60mg PO q6h PRN
- Prednisone 10mg PO daily
- Lisinopril 10mg PO daily
- Omeprazole 20mg PO daily

Recent History:
Progressive proximal muscle weakness and ptosis over 2 weeks.
Neurology recommends IVIG for rapid symptomatic control.
```

### 7.2 输出示例（Care Plan 结构）

**Problem List**
- Generalized myasthenia gravis (AChR antibody positive, MGFA IIb) — active
- Proximal muscle weakness with ptosis — subacute progression
- Hypertension — well controlled on Lisinopril
- GERD — managed with Omeprazole

**Goals**
- Achieve rapid symptomatic improvement of weakness and ptosis within 2–4 weeks of IVIG initiation
- Maintain stable MG control and reduce corticosteroid burden over 3–6 months
- Prevent IVIG-related adverse effects (headache, thrombosis, hemolysis)

**Pharmacist Interventions**
- Verify IVIG dose/infusion rate per body weight (standard: 2g/kg over 2–5 days)
- Counsel patient on pre-medication (acetaminophen, diphenhydramine) to reduce infusion reactions
- Review drug interactions with current immunosuppressant regimen
- Coordinate with neurology for follow-up and reassessment

**Monitoring Plan**
- Infusion vitals every 30 min during IVIG administration
- CBC, BMP, LFTs at baseline and 4 weeks post-infusion
- MG symptom scale assessment (MGFA) at 2 and 4 weeks
- Blood pressure monitoring weekly (per HTN management)

---

## 8. 导出与报告

| 导出类型 | 格式 | 用途 |
|----------|------|------|
| Care Plan 下载 | TXT / PDF | 打印交给患者；上传到内部系统 |
| Pharma 报告导出 | CSV / Excel | 报告给药厂（含 Provider NPI、患者数、用药量） |

报告字段至少包含：Provider NPI、Provider Name、Patient MRN、Medication、Order Date、Care Plan Generated (Y/N)。

---

## 9. 非功能性需求（Production-Ready）

| 类别 | 要求 |
|------|------|
| 输入验证 | 所有字段服务端验证，返回明确错误消息 |
| 数据完整性 | 数据库层面强制约束（唯一键、外键） |
| 错误处理 | LLM 调用失败需优雅降级，不丢失已录入数据 |
| 安全性 | PHI 数据加密传输（HTTPS），访问控制（角色权限） |
| 可维护性 | 模块化代码（表单、验证、LLM 调用、报告分层） |
| 测试覆盖 | 重复检测逻辑、验证规则、LLM 输出解析需单元测试覆盖 |
| 本地运行 | `README` 提供一键启动，端到端可运行 |

---

## 10. 技术栈建议（供参考）

| 层 | 建议 |
|----|------|
| Frontend | React + Tailwind（表单 + 警告弹窗） |
| Backend | FastAPI（Python）或 Node.js/Express |
| Database | PostgreSQL（强约束 + JSON 字段支持） |
| LLM | Anthropic Claude API 或 OpenAI GPT-4 |
| PDF 生成 | ReportLab（Python）或 Puppeteer（Node） |
| 测试 | pytest / Jest |

---

## 11. Open Questions

- [ ] LLM 输出是否需要药剂师人工审核后才能下载？
- [ ] Care Plan 是否需要版本控制（更新后保留历史）？
- [ ] Pharma 报告的具体字段和频率由谁定义？
- [ ] 系统是否需要 EHR 集成（HL7 / FHIR）？
- [ ] HIPAA 合规审计日志是否在范围内？