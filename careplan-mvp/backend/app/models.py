import uuid
from django.db import models


class Patient(models.Model):
    """病人表"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=50, unique=True, db_index=True)
    dob = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patients"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mrn})"


class ReferringProvider(models.Model):
    """医生 / 转诊医生表"""
    name = models.CharField(max_length=200)
    npi = models.CharField(max_length=20, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "referring_providers"

    def __str__(self):
        return f"{self.name} (NPI: {self.npi})"


class Order(models.Model):
    """订单表"""
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="orders")
    referring_provider = models.ForeignKey(
        ReferringProvider, on_delete=models.PROTECT, related_name="orders"
    )
    primary_diagnosis = models.CharField(max_length=50, blank=True)
    additional_diagnoses = models.JSONField(default=list)  # ["I10", "K21.0"]
    medication_name = models.CharField(max_length=200, blank=True)
    medication_history = models.JSONField(default=list)  # ["Prednisone 10mg", ...]
    patient_records = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "orders"
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.uuid)


class CarePlan(models.Model):
    """Care Plan 表，与 Order 一对一，带状态"""
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="care_plan"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    problem_list = models.JSONField(default=list, null=True, blank=True)
    goals = models.JSONField(default=list, null=True, blank=True)
    pharmacist_interventions = models.JSONField(default=list, null=True, blank=True)
    monitoring_plan = models.JSONField(default=list, null=True, blank=True)
    error_message = models.TextField(blank=True)  # 当 status=failed 时可选
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "care_plans"

    def __str__(self):
        return f"CarePlan(order={self.order_id}, status={self.status})"
