"""
Business logic: create order + care plan, enqueue task, etc.
No HTTP, no request/response. Reusable from views, tasks, CLI.
"""
from datetime import date

from .models import CarePlan, Order, Patient, ReferringProvider
from .tasks import generate_care_plan_task


def create_order_and_enqueue_care_plan(body: dict) -> tuple[Order, CarePlan]:
    """
    Create Patient/Provider if needed, Order, CarePlan (pending), enqueue task.
    Returns (order, care_plan). Raises ValueError if body invalid.
    """
    mrn = (body.get("patient_mrn") or "").strip()
    npi = (body.get("referring_provider_npi") or "").strip()
    if not mrn or not npi:
        raise ValueError("patient_mrn and referring_provider_npi are required")

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
    care_plan = CarePlan.objects.create(
        order=order, status=CarePlan.Status.PENDING
    )
    generate_care_plan_task.delay(care_plan.id)
    return order, care_plan
