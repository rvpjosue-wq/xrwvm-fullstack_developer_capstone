from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from datetime import datetime
import logging
import json

from .populate import initiate
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

logger = logging.getLogger(__name__)

# -------------------------
# LOGIN
# -------------------------
@csrf_exempt
def login_user(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = data.get("userName")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "Missing credentials"}, status=400)

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse({"status": "Invalid credentials"}, status=401)

    login(request, user)
    return JsonResponse({"userName": username, "status": "Authenticated"})
    

# -------------------------
# LOGOUT
# -------------------------
@csrf_exempt
def logout_request(request):
    logout(request)
    return JsonResponse({"status": "Logged out"})


# -------------------------
# REGISTRATION
# -------------------------
@csrf_exempt
def registration(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    username = data.get("userName")
    password = data.get("password")
    first_name = data.get("firstName", "")
    last_name = data.get("lastName", "")
    email = data.get("email", "")

    if not username or not password:
        return JsonResponse({"error": "Missing username or password"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Already Registered"}, status=409)

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        email=email
    )

    login(request, user)
    return JsonResponse({"userName": username, "status": "Authenticated"})


# -------------------------
# DEALERSHIPS
# -------------------------
def get_dealerships(request, state="All"):
    endpoint = "/fetchDealers" if state == "All" else f"/fetchDealers/{state}"
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


# -------------------------
# DEALER REVIEWS
# -------------------------
def get_dealer_reviews(request, dealer_id):
    if not dealer_id:
        return JsonResponse({"status": 400, "message": "Bad Request"})

    endpoint = f"/fetchReviews/dealer/{dealer_id}"
    reviews = get_request(endpoint)

    for review_detail in reviews:
        sentiment = analyze_review_sentiments(review_detail["review"])
        review_detail["sentiment"] = sentiment["sentiment"]

    return JsonResponse({"status": 200, "reviews": reviews})


# -------------------------
# DEALER DETAILS
# -------------------------
def get_dealer_details(request, dealer_id):
    if not dealer_id:
        return JsonResponse({"status": 400, "message": "Bad Request"})

    endpoint = f"/fetchDealer/{dealer_id}"
    dealership = get_request(endpoint)
    return JsonResponse({"status": 200, "dealer": dealership})


# -------------------------
# ADD REVIEW
# -------------------------
@csrf_exempt
def add_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": 403, "message": "Unauthorized"})

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"status": 400, "message": "Invalid JSON"})

    try:
        post_review(data)
        return JsonResponse({"status": 200})
    except Exception as e:
        logger.error(f"Review post failed: {e}")
        return JsonResponse({"status": 500, "message": "Error posting review"})


# -------------------------
# GET CARS
# -------------------------
def get_cars(request):
    if CarMake.objects.count() == 0:
        initiate()

    car_models = CarModel.objects.select_related("car_make")
    cars = [{"CarModel": cm.name, "CarMake": cm.car_make.name} for cm in car_models]

    return JsonResponse({"CarModels": cars})

