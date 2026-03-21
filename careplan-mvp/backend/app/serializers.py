"""
Data format conversion: API request/response ↔ Python/ORM.
Frontend JSON shape ↔ backend models/dicts. No HTTP, no business logic.
"""
import json

from .models import CarePlan, Order


def parse_request_body(body: bytes) -> dict:
    """Parse JSON request body to dict. Raises json.JSONDecodeError."""
    return json.loads(body)


def validate_generate_care_plan_body(body: dict) -> None:
    """Validate body for generate-care-plan. Raises ValueError if invalid."""
    mrn = (body.get("patient_mrn") or "").strip()
    npi = (body.get("referring_provider_npi") or "").strip()
    if not mrn or not npi:
        raise ValueError("patient_mrn and referring_provider_npi are required")


def build_generate_care_plan_response(order, care_plan) -> dict:
    """Build JSON response for POST /api/generate-care-plan/."""
    return {
        "message": "已收到",
        "order_id": str(order.uuid),
        "care_plan_id": care_plan.id,
    }


def order_to_response_dict(order: Order) -> dict:
    """Order + CarePlan → JSON shape for frontend (GET order detail)."""
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
        "care_plan_id": cp.id if cp else None,
        "patient_first_name": order.patient.first_name,
        "patient_last_name": order.patient.last_name,
        "patient_mrn": order.patient.mrn,
        "patient_dob": (
            order.patient.dob.isoformat() if order.patient.dob else ""
        ),
        "referring_provider": order.referring_provider.name,
        "referring_provider_npi": order.referring_provider.npi,
        "primary_diagnosis": order.primary_diagnosis,
        "additional_diagnoses": order.additional_diagnoses,
        "medication_name": order.medication_name,
        "medication_history": order.medication_history,
        "patient_records": order.patient_records,
        "care_plan": care_plan,
    }


def order_to_list_item(o: Order) -> dict:
    """Serialize Order to the list-item shape (GET orders list)."""
    return {
        "order_id": str(o.uuid),
        "created_at": o.created_at.isoformat(),
        "patient_name": f"{o.patient.first_name} {o.patient.last_name}",
        "medication_name": o.medication_name,
    }


def care_plan_to_status_payload(care_plan: CarePlan) -> dict:
    """CarePlan → status API response (GET careplan/<id>/status/)."""
    payload = {"status": care_plan.status}
    if care_plan.status == CarePlan.Status.COMPLETED:
        payload["content"] = {
            "problem_list": care_plan.problem_list or [],
            "goals": care_plan.goals or [],
            "pharmacist_interventions": (
                care_plan.pharmacist_interventions or []
            ),
            "monitoring_plan": care_plan.monitoring_plan or [],
        }
    elif care_plan.status == CarePlan.Status.FAILED:
        payload["error_message"] = care_plan.error_message or "Unknown error"
    return payload
