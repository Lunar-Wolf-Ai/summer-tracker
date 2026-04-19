# tracker/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard — home page
    path('', views.dashboard, name='dashboard'),

    # Goal management
    path('goals/set/', views.set_goal, name='set_goal'),
    path('goals/<int:goal_id>/toggle/', views.toggle_goal_complete, name='toggle_goal_complete'),

    # Daily logging
    path('log/', views.log_progress, name='log_progress'),
]