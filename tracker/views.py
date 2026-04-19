# tracker/views.py

from django.db import IntegrityError
import datetime
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from .models import Category, WeeklyGoal, DailyLog
from .forms import WeeklyGoalForm, DailyLogForm


def get_current_week_start():
    """Returns the Monday of the current week as a date object."""
    today = timezone.localdate()
    return today - datetime.timedelta(days=today.weekday())


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────

def dashboard(request):
    """
    Main dashboard view.
    Shows all active weekly goals with progress bars and a Chart.js bar chart.
    """
    week_start = get_current_week_start()
    week_end = week_start + datetime.timedelta(days=6)
    today = timezone.localdate()

    # Fetch this week's goals with related category data (avoids N+1 queries)
    weekly_goals = WeeklyGoal.objects.filter(
        week_start_date=week_start
    ).select_related('category').prefetch_related('daily_logs')

    # Build goal cards data — each dict powers one card + chart segment
    goal_cards = []
    chart_labels = []
    chart_hours_logged = []
    chart_hours_target = []
    chart_colors = []

    total_hours_logged = 0
    total_hours_target = 0

    for goal in weekly_goals:
        logged = float(goal.hours_logged)
        target = float(goal.target_hours)
        total_hours_logged += logged
        total_hours_target += target

        goal_cards.append({
            'goal': goal,
            'logged': logged,
            'target': target,
            'pct': goal.progress_percentage,
            'on_track': goal.is_on_track,
            'color': goal.category.color_code,
            'recent_logs': goal.daily_logs.order_by('-date')[:3],
        })

        # Chart.js data arrays
        chart_labels.append(goal.category.get_name_display())
        chart_hours_logged.append(logged)
        chart_hours_target.append(target)
        chart_colors.append(goal.category.color_code)

    # Recent logs across all goals for the activity feed
    recent_logs = DailyLog.objects.filter(
        weekly_goal__week_start_date=week_start
    ).select_related('weekly_goal__category').order_by('-date', '-created_at')[:10]

    # Overall week progress percentage
    overall_pct = 0
    if total_hours_target > 0:
        overall_pct = min(int((total_hours_logged / total_hours_target) * 100), 100)

    context = {
        'week_start': week_start,
        'week_end': week_end,
        'today': today,
        'goal_cards': goal_cards,
        'recent_logs': recent_logs,
        'total_hours_logged': round(total_hours_logged, 1),
        'total_hours_target': round(total_hours_target, 1),
        'overall_pct': overall_pct,
        'has_goals': weekly_goals.exists(),
        # Pass as JSON strings — consumed directly by Chart.js in the template
        'chart_labels_json': json.dumps(chart_labels),
        'chart_logged_json': json.dumps(chart_hours_logged),
        'chart_target_json': json.dumps(chart_hours_target),
        'chart_colors_json': json.dumps(chart_colors),
    }
    return render(request, 'tracker/dashboard.html', context)


# ─────────────────────────────────────────────
#  WEEKLY GOAL SETUP
# ─────────────────────────────────────────────

def set_goal(request):
    if request.method == 'POST':
        form = WeeklyGoalForm(request.POST)
        if form.is_valid():
            try:
                goal = form.save()
                messages.success(
                    request,
                    f"✅ Goal set for {goal.category.get_name_display()} this week!"
                )
                return redirect('dashboard')
            except IntegrityError:
                # Fires when a goal for this category+week already exists
                messages.error(
                    request,
                    "⚠️ A goal for this domain already exists this week. "
                    "Delete the existing one from admin first, or choose a different domain."
                )
        else:
            messages.error(request, "⚠️ Please fix the errors below.")

    else:
        form = WeeklyGoalForm()

    week_start = get_current_week_start()
    existing_goals = WeeklyGoal.objects.filter(
        week_start_date=week_start
    ).select_related('category')

    context = {
        'form': form,
        'existing_goals': existing_goals,
        'week_start': week_start,
    }
    return render(request, 'tracker/set_goal.html', context)


# ─────────────────────────────────────────────
#  DAILY LOG
# ─────────────────────────────────────────────

def log_progress(request):
    """
    End-of-day log submission view.
    On GET: renders the log form with today's date pre-filled.
    On POST: validates, saves, and redirects to dashboard.
    """
    if request.method == 'POST':
        form = DailyLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(
                request,
                f"🎯 Logged {log.hours_spent}h for {log.weekly_goal.category.get_name_display()} on {log.date}!"
            )
            return redirect('dashboard')
        else:
            messages.error(request, "⚠️ Please fix the errors below.")
    else:
        form = DailyLogForm()

    # Pass this week's goals summary alongside the form
    week_start = get_current_week_start()
    active_goals = WeeklyGoal.objects.filter(
        week_start_date=week_start
    ).select_related('category')

    context = {
        'form': form,
        'active_goals': active_goals,
        'today': timezone.localdate(),
    }
    return render(request, 'tracker/log_progress.html', context)


# ─────────────────────────────────────────────
#  GOAL TOGGLE — AJAX-FRIENDLY QUICK ACTION
# ─────────────────────────────────────────────

def toggle_goal_complete(request, goal_id):
    """
    POST-only view to mark a weekly goal as completed/incomplete.
    Called via a button on the dashboard card.
    """
    if request.method == 'POST':
        goal = get_object_or_404(WeeklyGoal, id=goal_id)
        goal.is_completed = not goal.is_completed
        goal.save(update_fields=['is_completed'])
        status = "completed ✅" if goal.is_completed else "reopened 🔄"
        messages.success(
            request,
            f"{goal.category.get_name_display()} goal marked as {status}."
        )
    return redirect('dashboard')