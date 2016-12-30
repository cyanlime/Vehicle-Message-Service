import json
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from account.common import (
    fetch_token,
    render_bad_request_response,
    get_vehicle_by_id, 
    vehicle_token_authenticate
    )
from django.views.decorators.csrf import csrf_exempt
from .models import Point

# Create your views here.

@csrf_exempt
@require_http_methods(["POST"])
def sync_points(request):
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (vehicle_id, err) = vehicle_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    vehicle = get_vehicle_by_id(vehicle_id)
    if vehicle is None:
        return render_bad_request_response(303, 'Unknown vehicle')
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')
    if type(request_json) is not list:
        return render_bad_request_response(101, \
            'Incorrect data format. Require list but %s' % type(request_json).__name__)
    points = []
    for point in request_json:
        if point is None:
            return render_bad_request_response(101, 'Incorrect data format')
        lat = point.get('lat', None)
        lon = point.get('lon', None)
        if lat is None or lon is None:
            return render_bad_request_response(101, 'Incorrect data format')
        points.append(Point(vehicle=vehicle, latitude=lat, longitude=lon))
    Point.objects.bulk_create(points)
    json_context = json.dumps({
        'errcode': 0,
        'ok': 1
    })
    return HttpResponse(
        json_context, content_type='application/json'
    )
        