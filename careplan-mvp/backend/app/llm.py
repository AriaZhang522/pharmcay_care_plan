"""Call Claude to generate care plan JSON. Used by views and Celery task."""
import json

import anthropic
from django.conf import settings


def _fake_care_plan(order_dict: dict) -> dict:
    """Return a fixed care plan without calling any API. Same shape as real LLM response."""
    name = f"{order_dict.get('patient_first_name', '')} {order_dict.get('patient_last_name', '')}".strip() or "Patient"
    return {
        "problem_list": [
            f"Primary diagnosis: {order_dict.get('primary_diagnosis', 'N/A')}",
            "Polypharmacy / medication adherence concerns",
            "Need for ongoing monitoring",
        ],
        "goals": [
            f"Optimize therapy for {name} per care plan",
            "Improve adherence and health literacy",
            "Reduce risk of adverse events",
        ],
        "pharmacist_interventions": [
            "Initial comprehensive medication review completed",
            "Patient education on medication and monitoring",
            "Coordinate with referring provider as needed",
        ],
        "monitoring_plan": [
            "Labs per protocol and diagnosis",
            "Follow-up in 30 days or as clinically indicated",
            "Document interventions in EMR",
        ],
    }


def call_llm_for_care_plan(order_dict: dict) -> dict:
    if getattr(settings, "USE_FAKE_LLM", False):
        return _fake_care_plan(order_dict)

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    prompt = f"""You are a clinical pharmacist at a specialty pharmacy generating a Medicare-compliant care plan.

Patient Information:
- Name: {order_dict["patient_first_name"]} {order_dict["patient_last_name"]}
- MRN: {order_dict["patient_mrn"]}
- Primary Diagnosis (ICD-10): {order_dict["primary_diagnosis"]}
- Additional Diagnoses: {", ".join(order_dict["additional_diagnoses"]) if order_dict["additional_diagnoses"] else "None"}
- Medication: {order_dict["medication_name"]}
- Medication History: {"; ".join(order_dict["medication_history"]) if order_dict["medication_history"] else "None"}
- Referring Provider: {order_dict["referring_provider"]} (NPI: {order_dict["referring_provider_npi"]})

Patient Records / Clinical Notes:
{order_dict["patient_records"]}

Generate a structured care plan with exactly these four sections.
Respond ONLY with a valid JSON object, no markdown, no extra text.

{{
  "problem_list": ["problem 1", "problem 2", "..."],
  "goals": ["goal 1", "goal 2", "..."],
  "pharmacist_interventions": ["intervention 1", "intervention 2", "..."],
  "monitoring_plan": ["monitoring item 1", "monitoring item 2", "..."]
}}
"""
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)
