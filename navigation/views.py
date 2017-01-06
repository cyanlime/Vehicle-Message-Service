import json, datetime, time
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from account.common import (
    fetch_token,
    render_bad_request_response,
    get_vehicle_by_id, 
    vehicle_token_authenticate,
    get_wechat_by_id, 
    wechat_token_authenticate
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
    
    points = []
    LineArrs = request_json.get('lineArr')
    if type(LineArrs) is not list:
        return render_bad_request_response(101, \
            'Incorrect data format. Require list but %s' % type(request_json).__name__)

    for linearr in LineArrs:
        if linearr is None or len(linearr)!=5:
            #return render_bad_request_response(101, 'Incorrect data format')
            accounts_position = {'code': 1, 'result': {'msg': "Incoming parameter lineArr ValueError."}}
            return JsonResponse(accounts_position)

        timestamp_position_time = linearr[4]
        position_time = datetime.datetime.fromtimestamp(int(timestamp_position_time))

        points.append(Point(vehicle=vehicle, longitude=linearr[0], latitude=linearr[1], 
            bearing=linearr[2], speed=linearr[3], time=position_time))
    Point.objects.bulk_create(points)
    # json_context = json.dumps({
    #     'errcode': 0,
    #     'ok': 1
    # })
    # return HttpResponse(
    #     json_context, content_type='application/json'
    # )

    accounts_position = {'code': 0, 'result': {'msg': "Location information upload successfully."}}
    return JsonResponse(accounts_position)


@csrf_exempt
@require_http_methods(["GET"])
def current_point(request):
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (wechat_id, err) = wechat_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    wechat = get_wechat_by_id(wechat_id)
    if wechat.vehicle is None:
        return render_bad_request_response(201, 'No related vehicle found')
    point = Point.objects.filter(vehicle=wechat.vehicle).order_by('-time').first()
    if point is None:
        json_context = json.dumps({
            'errcode': 100,
            'errmsg': 'No data found'
        })
    else:
        timestamp_point_vehicle_createtime = time.mktime(point.vehicle.create_time.timetuple())
        timestamp_point_time = time.mktime(point.time.timetuple())

        json_context = json.dumps({
            'code': 0,
            'result': {'id': point.id, 'account': {'vehicle_id': point.vehicle.id, 'vin': point.vehicle.vin, 
                'create_time': timestamp_point_vehicle_createtime},
                'longitude': point.longitude, 'latitude': point.latitude, 'bearing': point.bearing,
                'speed': point.speed, 'time': timestamp_point_time}
        })
    return HttpResponse(
        json_context, content_type='application/json'
    )

@csrf_exempt
@require_http_methods(["GET"])
def series_point(request):
    token = fetch_token(request)
    if token is None:
        return render_bad_request_response(301, 'Missing authorization header')
    (wechat_id, err) = wechat_token_authenticate(token)
    if err is not None:
        return render_bad_request_response(302, err)
    wechat = get_wechat_by_id(wechat_id)
    if wechat.vehicle is None:
        return render_bad_request_response(201, 'No related vehicle found')
    try:
        request_json = json.loads(request.body)
    except ValueError:
        return render_bad_request_response(101, 'Incorrect json format')

    Date = request_json.get('date')
    if len(Date)!=8:
        account_traces = {'code': 1, 'result': {'errmsg': "Incorrect incoming parameter date."}}
        return JsonResponse(account_traces)

    specified_year = int(Date[:4])
    specified_month = int(Date[4:6])
    specified_day = int(Date[6:8])
    try:
        specified_date = datetime.datetime(specified_year, specified_month, specified_day)
    except ValueError:
        account_traces = {'code': 1, 'result': {'errmsg': "Incorrect incoming parameter date value."}}
        return JsonResponse(account_traces)
 
    day_after_specified_date = specified_date+datetime.timedelta(hours=24)
    date_today_date = datetime.date.today()
    date_today = datetime.datetime(date_today_date.year, date_today_date.month, date_today_date.day)

    if specified_date<date_today:
        start_date = specified_date
        end_date = day_after_specified_date 
    else:
        start_date = date_today
        end_date = datetime.datetime.now()
    
    point_set = []
    points = Point.objects.filter(vehicle=wechat.vehicle).filter(time__range=(start_date, end_date))
    for point in points:
        point_time = point.time
        timestamp_point_time = time.mktime(point_time.timetuple())
        serialize_point = {'id': point.id , 'longitude': point.longitude, 'latitude': point.latitude, 
            'bearing': point.bearing, 'speed': point.speed, 'time': timestamp_point_time}
        point_set.append(serialize_point)
    wechat_vehicle_createtime = wechat.vehicle.create_time
    timestamp_point_time = time.mktime(wechat_vehicle_createtime.timetuple())
    account_traces = {'code': 0, 'result': {'points': point_set, 'account': {
        'vehicle_id': wechat.vehicle.id, 'vin': wechat.vehicle.vin, 'create_time': wechat_vehicle_createtime}}}
    return JsonResponse(account_traces)
