from django.urls import path
from .views import intelligence

urlpatterns = [
    path("intelligence/", intelligence),
]