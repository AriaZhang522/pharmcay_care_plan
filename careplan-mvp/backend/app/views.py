import json
from datetime import date

import anthropic
import redis
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import CarePlan, Order, Patient, ReferringProvider


# ─────────────────────────────────────────────
# Helper: call Claude to generate care plan (same prompt shape as before)
# ─────────────────────────────────────────────
def call_llm_for_care_plan(order_dict: dict) -> dict:
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


def _order_to_response_dict(order: Order) -> dict:
    """Serialize Order + CarePlan to the same JSON shape the frontend expects."""
    cp = getattr(order, "care_plan", None)
    care_plan = None
    if cp and cp.status == CarePlan.Status.COMPLETED:
        care_plan = {
            "problem_list": cp.problem_list or [],
            "goals": cp.goals or [],
            "pharmacist_interventions": cp.pharmacist_interventions or [],
            "monitoring_plan": cp.monitoring_plan or [],
        }
    return {
        "order_id": str(order.uuid),
        "created_at": order.created_at.isoformat(),
        "patient_first_name": order.patient.first_name,
        "patient_last_name": order.patient.last_name,
        "patient_mrn": order.patient.mrn,
        "patient_dob": order.patient.dob.isoformat() if order.patient.dob else "",
        "referring_provider": order.referring_provider.name,
        "referring_provider_npi": order.referring_provider.npi,
        "primary_diagnosis": order.primary_diagnosis,
        "additional_diagnoses": order.additional_diagnoses,
        "medication_name": order.medication_name,
        "medication_history": order.medication_history,
        "patient_records": order.patient_records,
        "care_plan": care_plan,
    }


# ─────────────────────────────────────────────
# POST /api/generate-care-plan/
# Async: save CarePlan (pending) → push care_plan_id to Redis queue → return immediately.
# Worker (not implemented yet) will pop from queue and call LLM.
# ─────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def generate_care_plan(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    mrn = (body.get("patient_mrn") or "").strip()
    npi = (body.get("referring_provider_npi") or "").strip()
    if not mrn or not npi:
        return JsonResponse(
            {"error": "patient_mrn and referring_provider_npi are required"},
            status=400,
        )

    dob = body.get("patient_dob")
    if dob:
        try:
            dob = date.fromisoformat(dob) if isinstance(dob, str) else dob
        except (TypeError, ValueError):
            dob = None

    patient, _ = Patient.objects.get_or_create(
        mrn=mrn,
        defaults={
            "first_name": body.get("patient_first_name", ""),
            "last_name": body.get("patient_last_name", ""),
            "dob": dob,
        },
    )
    provider, _ = ReferringProvider.objects.get_or_create(
        npi=npi,
        defaults={"name": body.get("referring_provider", "")},
    )

    order = Order.objects.create(
        patient=patient,
        referring_provider=provider,
        primary_diagnosis=body.get("primary_diagnosis", ""),
        additional_diagnoses=body.get("additional_diagnoses", []) or [],
        medication_name=body.get("medication_name", ""),
        medication_history=body.get("medication_history", []) or [],
        patient_records=body.get("patient_records", ""),
    )
    care_plan_obj = CarePlan.objects.create(order=order, status=CarePlan.Status.PENDING)

    # Push care_plan_id to Redis queue (worker will pop and process later)
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )
        r.lpush(settings.REDIS_QUEUE_KEY, str(care_plan_obj.id))
    except redis.RedisError as e:
        care_plan_obj.status = CarePlan.Status.FAILED
        care_plan_obj.error_message = f"Queue error: {e}"
        care_plan_obj.save(update_fields=["status", "error_message", "updated_at"])
        return JsonResponse(
            {"error": "Failed to enqueue job"}, status=500
        )

    return JsonResponse({
        "message": "已收到",
        "order_id": str(order.uuid),
    })


# ─────────────────────────────────────────────
# GET /api/orders/
# Returns list of orders (for history panel)
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def list_orders(request):
    orders = Order.objects.select_related("patient").order_by("-created_at")
    orders_list = [
        {
            "order_id": str(o.uuid),
            "created_at": o.created_at.isoformat(),
            "patient_name": f"{o.patient.first_name} {o.patient.last_name}",
            "medication_name": o.medication_name,
        }
        for o in orders
    ]
    return JsonResponse({"orders": orders_list})


# ─────────────────────────────────────────────
# GET /api/orders/<order_id>/
# Returns full order (incl. care_plan) for the given order_id, or 404.
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def get_order(request, order_id):
    order = (
        Order.objects.filter(uuid=order_id)
        .select_related("patient", "referring_provider", "care_plan")
        .first()
    )
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)
    return JsonResponse(_order_to_response_dict(order))
