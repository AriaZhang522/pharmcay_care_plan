"""
Hand-written worker: pull care_plan_id from Redis → call LLM → save result to DB.
Run: python manage.py run_care_plan_worker
In Docker: worker service runs this in a loop.
"""
import redis
from django.conf import settings
from django.core.management.base import BaseCommand

from app.models import CarePlan
from app.llm import call_llm_for_care_plan


class Command(BaseCommand):
    help = "Pull jobs from Redis queue, call LLM, save care plan to DB. No Celery."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=5,
            help="Redis BRPOP timeout in seconds (default 5).",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True,
        )
        queue_key = settings.REDIS_QUEUE_KEY
        self.stdout.write(f"Worker started. Waiting for jobs on Redis list '{queue_key}' (BRPOP timeout={timeout}s).")

        while True:
            # BRPOP: block until an item is available, or timeout
            result = r.brpop(queue_key, timeout=timeout)
            if result is None:
                # Timeout, no job; loop again
                continue

            # result is (list_name, value) e.g. ("care_plan_queue", "42")
            _, care_plan_id_str = result
            care_plan_id = int(care_plan_id_str)

            self.stdout.write(f"Got job care_plan_id={care_plan_id}")

            try:
                care_plan = (
                    CarePlan.objects.filter(id=care_plan_id)
                    .select_related("order__patient", "order__referring_provider")
                    .first()
                )
                if not care_plan:
                    self.stderr.write(f"CarePlan id={care_plan_id} not found, skip.")
                    continue

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

                result_data = call_llm_for_care_plan(order_dict)
                care_plan.problem_list = result_data.get("problem_list", [])
                care_plan.goals = result_data.get("goals", [])
                care_plan.pharmacist_interventions = result_data.get("pharmacist_interventions", [])
                care_plan.monitoring_plan = result_data.get("monitoring_plan", [])
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
                self.stdout.write(self.style.SUCCESS(f"CarePlan id={care_plan_id} completed."))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"CarePlan id={care_plan_id} failed: {e}"))
                try:
                    care_plan = CarePlan.objects.get(id=care_plan_id)
                    care_plan.status = CarePlan.Status.FAILED
                    care_plan.error_message = str(e)
                    care_plan.save(update_fields=["status", "error_message", "updated_at"])
                except Exception:
                    pass
