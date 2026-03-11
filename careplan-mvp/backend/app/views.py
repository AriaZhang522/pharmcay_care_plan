"""
HTTP layer: receive request, call serializer/service, return JsonResponse.
No business logic here; only parsing, validation of HTTP input, and response shape.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import CarePlan, Order
from .serializers import (
    care_plan_to_status_payload,
    order_to_list_item,
    order_to_response_dict,
)
from .services import create_order_and_enqueue_care_plan


# ─────────────────────────────────────────────
# POST /api/generate-care-plan/
# ─────────────────────────────────────────────
@csrf_exempt
@require_http_methods(["POST"])
def generate_care_plan(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        order, care_plan = create_order_and_enqueue_care_plan(body)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({
        "message": "已收到",
        "order_id": str(order.uuid),
        "care_plan_id": care_plan.id,
    })


# ─────────────────────────────────────────────
# GET /api/orders/
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def list_orders(request):
    orders = Order.objects.select_related("patient").order_by("-created_at")
    orders_list = [order_to_list_item(o) for o in orders]
    return JsonResponse({"orders": orders_list})


# ─────────────────────────────────────────────
# GET /api/careplan/<id>/status/
# ─────────────────────────────────────────────
@require_http_methods(["GET"])
def care_plan_status(request, id):
    care_plan = CarePlan.objects.filter(id=id).first()
    if not care_plan:
        return JsonResponse({"error": "Care plan not found"}, status=404)
    return JsonResponse(care_plan_to_status_payload(care_plan))


# ─────────────────────────────────────────────
# GET /api/orders/<order_id>/
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
    return JsonResponse(order_to_response_dict(order))
