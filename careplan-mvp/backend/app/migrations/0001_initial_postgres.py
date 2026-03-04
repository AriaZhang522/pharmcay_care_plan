# Generated manually for PostgreSQL schema

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Patient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("mrn", models.CharField(db_index=True, max_length=50, unique=True)),
                ("dob", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "patients"},
        ),
        migrations.CreateModel(
            name="ReferringProvider",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("npi", models.CharField(db_index=True, max_length=20, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "referring_providers"},
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("uuid", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("primary_diagnosis", models.CharField(blank=True, max_length=50)),
                ("additional_diagnoses", models.JSONField(default=list)),
                ("medication_name", models.CharField(blank=True, max_length=200)),
                ("medication_history", models.JSONField(default=list)),
                ("patient_records", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="app.patient")),
                ("referring_provider", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to="app.referringprovider")),
            ],
            options={"db_table": "orders", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CarePlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], db_index=True, default="pending", max_length=20)),
                ("problem_list", models.JSONField(blank=True, default=list, null=True)),
                ("goals", models.JSONField(blank=True, default=list, null=True)),
                ("pharmacist_interventions", models.JSONField(blank=True, default=list, null=True)),
                ("monitoring_plan", models.JSONField(blank=True, default=list, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="care_plan", to="app.order")),
            ],
            options={"db_table": "care_plans"},
        ),
    ]
