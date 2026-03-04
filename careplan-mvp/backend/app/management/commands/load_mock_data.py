"""
Load mock patients, providers, orders, and care plans into the database.
Usage (in Docker): docker compose exec backend python manage.py load_mock_data
Usage (local):     python manage.py load_mock_data
"""
import uuid
from datetime import date

from django.core.management.base import BaseCommand

from app.models import CarePlan, Order, Patient, ReferringProvider


MOCK_PATIENTS = [
    {"first_name": "Maria", "last_name": "Garcia", "mrn": "MRN-MOCK-001", "dob": date(1958, 3, 15)},
    {"first_name": "Robert", "last_name": "Kim", "mrn": "MRN-MOCK-002", "dob": date(1972, 8, 22)},
    {"first_name": "Patricia", "last_name": "Johnson", "mrn": "MRN-MOCK-003", "dob": date(1965, 11, 8)},
]

MOCK_PROVIDERS = [
    {"name": "Dr. James Chen", "npi": "1234567890"},
    {"name": "Dr. Sarah Williams", "npi": "1987654321"},
    {"name": "Dr. David Park", "npi": "1122334455"},
]

MOCK_ORDERS = [
    {
        "order_uuid": "a1000001-0001-4000-8000-000000000001",
        "mrn": "MRN-MOCK-001",
        "npi": "1234567890",
        "primary_diagnosis": "I10",
        "additional_diagnoses": ["E11.9", "E78.00"],
        "medication_name": "Lisinopril 10 mg daily",
        "medication_history": ["Amlodipine 5mg (discontinued)", "Metformin 500mg BID"],
        "patient_records": "68 y/o F with HTN, Type 2 DM, hyperlipidemia. BP 148/92. A1c 7.2%.",
    },
    {
        "order_uuid": "a1000002-0002-4000-8000-000000000002",
        "mrn": "MRN-MOCK-002",
        "npi": "1987654321",
        "primary_diagnosis": "M06.9",
        "additional_diagnoses": ["M17.11", "K21.0"],
        "medication_name": "Adalimumab 40 mg every 2 weeks",
        "medication_history": ["Methotrexate 15mg weekly", "Omeprazole 20mg daily"],
        "patient_records": "52 y/o M with rheumatoid arthritis, knee OA, GERD. Starting adalimumab.",
    },
    {
        "order_uuid": "a1000003-0003-4000-8000-000000000003",
        "mrn": "MRN-MOCK-003",
        "npi": "1122334455",
        "primary_diagnosis": "G20",
        "additional_diagnoses": ["F32.1", "G47.33"],
        "medication_name": "Carbidopa-Levodopa 25-100 mg TID",
        "medication_history": ["Pramipexole 0.25mg TID", "Sertraline 50mg daily"],
        "patient_records": "59 y/o F with Parkinson disease, depression, insomnia. Off periods reported.",
    },
]

MOCK_CARE_PLANS = [
    {
        "order_uuid": "a1000001-0001-4000-8000-000000000001",
        "problem_list": ["Uncontrolled hypertension (I10)", "Type 2 diabetes (E11.9)", "Hyperlipidemia (E78.00)"],
        "goals": ["Achieve BP <140/90 mmHg", "Maintain A1c <7%", "LDL-C at goal"],
        "pharmacist_interventions": ["Medication adherence counseling", "Review Metformin timing", "Discuss DASH diet"],
        "monitoring_plan": ["Home BP log weekly", "A1c every 3 months", "Lipid panel annually"],
    },
    {
        "order_uuid": "a1000002-0002-4000-8000-000000000002",
        "problem_list": ["Rheumatoid arthritis (M06.9)", "Knee OA (M17.11)", "GERD (K21.0)"],
        "goals": ["Reduce disease activity", "Minimize infection risk", "Control GERD"],
        "pharmacist_interventions": ["Infection signs education", "Injection technique for Adalimumab", "PPI timing"],
        "monitoring_plan": ["CBC, CMP, LFT periodically", "Monitor infections", "Rheumatology follow-up"],
    },
    {
        "order_uuid": "a1000003-0003-4000-8000-000000000003",
        "problem_list": ["Parkinson disease (G20)", "Depression (F32.1)", "Insomnia (G47.33)"],
        "goals": ["Optimize on-time with levodopa", "Reduce fall risk", "Stable mood and sleep"],
        "pharmacist_interventions": ["Levodopa on empty stomach 30-60 min before meals", "Drug-disease interactions with Sertraline", "Fall risk counseling"],
        "monitoring_plan": ["Document off-periods and dyskinesia", "MDS-UPDRS at neurology", "Mood and sleep log"],
    },
]


class Command(BaseCommand):
    help = "Load mock patients, providers, orders, and care plans (same data as mock_data.sql)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing orders and care plans before loading (keeps patients/providers).",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            CarePlan.objects.all().delete()
            Order.objects.all().delete()
            self.stdout.write("Cleared orders and care_plans.")

        # Patients
        for p in MOCK_PATIENTS:
            patient, created = Patient.objects.get_or_create(mrn=p["mrn"], defaults=p)
            self.stdout.write(f"  Patient {p['mrn']}: {'created' if created else 'exists'}")

        # Providers
        for pr in MOCK_PROVIDERS:
            provider, created = ReferringProvider.objects.get_or_create(npi=pr["npi"], defaults=pr)
            self.stdout.write(f"  Provider {pr['npi']}: {'created' if created else 'exists'}")

        # Orders + Care plans
        for o, cp in zip(MOCK_ORDERS, MOCK_CARE_PLANS):
            order_uuid = uuid.UUID(o["order_uuid"])
            if Order.objects.filter(uuid=order_uuid).exists():
                self.stdout.write(f"  Order {o['order_uuid'][:8]}…: exists, skip")
                continue
            patient = Patient.objects.get(mrn=o["mrn"])
            provider = ReferringProvider.objects.get(npi=o["npi"])
            order = Order.objects.create(
                uuid=order_uuid,
                patient=patient,
                referring_provider=provider,
                primary_diagnosis=o["primary_diagnosis"],
                additional_diagnoses=o["additional_diagnoses"],
                medication_name=o["medication_name"],
                medication_history=o["medication_history"],
                patient_records=o["patient_records"],
            )
            CarePlan.objects.create(
                order=order,
                status=CarePlan.Status.COMPLETED,
                problem_list=cp["problem_list"],
                goals=cp["goals"],
                pharmacist_interventions=cp["pharmacist_interventions"],
                monitoring_plan=cp["monitoring_plan"],
            )
            self.stdout.write(self.style.SUCCESS(f"  Order {o['order_uuid'][:8]}… + care_plan created."))

        self.stdout.write(self.style.SUCCESS("Mock data load done."))
