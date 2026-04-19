# tracker/admin.py

from django.contrib import admin
from .models import Category, WeeklyGoal, DailyLog


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code')


@admin.register(WeeklyGoal)
class WeeklyGoalAdmin(admin.ModelAdmin):
    list_display = ('category', 'week_start_date', 'target_hours', 'hours_logged', 'progress_percentage', 'is_completed')
    list_filter = ('category', 'is_completed', 'week_start_date')


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('weekly_goal', 'date', 'hours_spent')
    list_filter = ('date', 'weekly_goal__category')