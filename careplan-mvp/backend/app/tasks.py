"""
Celery task: generate care plan via LLM, update DB. Retry up to 3 times with exponential backoff.
"""
from celery import shared_task
from django.conf import settings

from app.models import CarePlan
from app.llm import call_llm_for_care_plan


@shared_task(bind=True, max_retries=3)
def generate_care_plan_task(self, care_plan_id: int):
    """
    Load CarePlan by id, call LLM, save result. On failure retry with exponential backoff (1s, 2s, 4s).
    """
    care_plan = (
        CarePlan.objects.filter(id=care_plan_id)
        .select_related("order__patient", "order__referring_provider")
        .first()
    )
    if not care_plan:
        return

    order = care_plan.order
    order_dict = {
        "patient_first_name": order.patient.first_name,
        "patient_last_name": order.patient.last_name,
        "patient_mrn": order.patient.mrn,
        "primary_diagnosis": order.primary_diagnosis,
        "additional_diagnoses": order.additional_diagnoses or [],
        "medication_name": order.medication_name,
        "medication_history": order.medication_history or [],
        "referring_provider": order.referring_provider.name,
        "referring_provider_npi": order.referring_provider.npi,
        "patient_records": order.patient_records or "",
    }

    care_plan.status = CarePlan.Status.PROCESSING
    care_plan.save(update_fields=["status", "updated_at"])

    try:
        result = call_llm_for_care_plan(order_dict)
        care_plan.problem_list = result.get("problem_list", [])
        care_plan.goals = result.get("goals", [])
        care_plan.pharmacist_interventions = result.get("pharmacist_interventions", [])
        care_plan.monitoring_plan = result.get("monitoring_plan", [])
        care_plan.status = CarePlan.Status.COMPLETED
        care_plan.save(
            update_fields=[
                "problem_list",
                "goals",
                "pharmacist_interventions",
                "monitoring_plan",
                "status",
                "updated_at",
            ]
        )
    except Exception as exc:
        care_plan.status = CarePlan.Status.FAILED
        care_plan.error_message = str(exc)
        care_plan.save(update_fields=["status", "error_message", "updated_at"])
        # Exponential backoff: 2^retries seconds (1, 2, 4)
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)
