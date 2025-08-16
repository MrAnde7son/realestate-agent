from django.urls import path
from . import views
urlpatterns = [ path('alerts/', views.alerts, name='alerts'), path('mortgage/analyze/', views.mortgage_analyze, name='mortgage_analyze'), ]
