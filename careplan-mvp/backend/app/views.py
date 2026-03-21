"""
HTTP layer: receive request, call serializer/service, return JsonResponse.
No business logic, no DB queries. Only: get request data → call service/serializer → return.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .serializers import (
    build_generate_care_plan_response,
    care_plan_to_status_payload,
    order_to_list_item,
    order_to_response_dict,
    parse_request_body,
    validate_generate_care_plan_body,
)
from .services import (
    create_order_and_enqueue_care_plan,
    get_all_orders_for_list,
    get_care_plan_by_id,
    get_order_by_uuid,
)


@csrf_exempt
@require_http_methods(["POST"])
def generate_care_plan(request):
    try:
        body = parse_request_body(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        validate_generate_care_plan_body(body)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    order, care_plan = create_order_and_enqueue_care_plan(body)
    return JsonResponse(build_generate_care_plan_response(order, care_plan))


@require_http_methods(["GET"])
def list_orders(request):
    orders = get_all_orders_for_list()
    return JsonResponse({"orders": [order_to_list_item(o) for o in orders]})


@require_http_methods(["GET"])
def care_plan_status(request, id):
    care_plan = get_care_plan_by_id(id)
    if not care_plan:
        return JsonResponse({"error": "Care plan not found"}, status=404)
    return JsonResponse(care_plan_to_status_payload(care_plan))


@require_http_methods(["GET"])
def get_order(request, order_id):
    order = get_order_by_uuid(order_id)
    if not order:
        return JsonResponse({"error": "Order not found"}, status=404)
    return JsonResponse(order_to_response_dict(order))
