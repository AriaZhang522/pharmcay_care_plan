from django.urls import path
from app import views

urlpatterns = [
    path("api/generate-care-plan/", views.generate_care_plan),
    path("api/orders/", views.list_orders),
]
