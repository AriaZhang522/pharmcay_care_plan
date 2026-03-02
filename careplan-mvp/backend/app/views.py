import json
import uuid
from datetime import datetime

import anthropic
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# ─────────────────────────────────────────────
# In-memory "database" — just a Python dict
# Resets every time the server restarts.
# ─────────────────────────────────────────────
ORDERS = {}  # { order_id: { ...order data + care_plan } }


# ─────────────────────────────────────────────
# Helper: call Claude to generate care plan
# ─────────────────────────────────────────────
def call_llm_for_care_plan(order: dict) -> dict:
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    prompt = f"""You are a clinical pharmacist at a specialty pharmacy generating a Medicare-compliant care plan.

Patient Information:
- Name: {order["patient_first_name"]} {order["patient_last_name"]}
- MRN: {order["patient_mrn"]}
- Primary Diagnosis (ICD-10): {order["primary_diagnosis"]}
- Additional Diagnoses: {", ".join(order["additional_diagnoses"]) if order["additional_diagnoses"] else "None"}
- Medication: {order["medication_name"]}
- Medication History: {"; ".join(order["medication_history"]) if order["medication_history"] else "None"}
- Referring Provider: {order["referring_provider"]} (NPI: {order["referring_provider_npi"]})

Patient Records / Clinical Notes:
{order["patient_records"]}

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

    # Strip markdown fences if the model wraps in ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


# ─────────────────────────────────────────────
# POST /api/generate-care-plan/
# Accepts form data, calls LLM, stores in memory, returns care plan
# ─────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def generate_care_plan(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Build order record
    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "created_at": datetime.utcnow().isoformat(),
        # Patient
        "patient_first_name": body.get("patient_first_name", ""),
        "patient_last_name": body.get("patient_last_name", ""),
        "patient_mrn": body.get("patient_mrn", ""),
        # Provider
        "referring_provider": body.get("referring_provider", ""),
        "referring_provider_npi": body.get("referring_provider_npi", ""),
        # Clinical
        "primary_diagnosis": body.get("primary_diagnosis", ""),
        "additional_diagnoses": body.get("additional_diagnoses", []),
        "medication_name": body.get("medication_name", ""),
        "medication_history": body.get("medication_history", []),
        "patient_records": body.get("patient_records", ""),
        # Care plan — filled in below
        "care_plan": None,
    }

    # Call LLM synchronously — user waits
    try:
        care_plan = call_llm_for_care_plan(order)
        order["care_plan"] = care_plan
    except Exception as e:
        return JsonResponse({"error": f"LLM generation failed: {str(e)}"}, status=500)

    # Store in memory
    ORDERS[order_id] = order

    return JsonResponse({
        "order_id": order_id,
        "care_plan": care_plan,
    })


# ─────────────────────────────────────────────
# GET /api/orders/
# Returns all orders stored in memory (for the history panel)
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def list_orders(request):
    orders_list = [
        {
            "order_id": o["order_id"],
            "created_at": o["created_at"],
            "patient_name": f"{o['patient_first_name']} {o['patient_last_name']}",
            "medication_name": o["medication_name"],
        }
        for o in ORDERS.values()
    ]
    # Most recent first
    orders_list.sort(key=lambda x: x["created_at"], reverse=True)
    return JsonResponse({"orders": orders_list})
