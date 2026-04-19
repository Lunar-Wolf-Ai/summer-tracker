# tracker/models.py

from django.db import models
from django.utils import timezone


class Category(models.Model):
    """
    Represents a study domain (e.g., DSA, Data Science, Robotics, EC).
    Each category has a display color used in charts and UI accents.
    """

    # Predefined choices keep the UI consistent and avoid typos
    DOMAIN_CHOICES = [
        ('DSA', 'Data Structures & Algorithms'),
        ('DS', 'Data Science'),
        ('ROB', 'Robotics'),
        ('EC', 'Electronics & Communication'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        choices=DOMAIN_CHOICES,
        help_text="The study domain this category represents."
    )

    # Stored as a hex string (e.g. '#4F46E5') — used by Chart.js and Tailwind
    color_code = models.CharField(
        max_length=7,
        default='#6B7280',
        help_text="Hex color code for UI and chart rendering (e.g. #4F46E5)."
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()


class WeeklyGoal(models.Model):
    """
    Represents a single goal for a specific category within a specific week.
    The week is always anchored to its Monday (week_start_date).
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='weekly_goals',
        help_text="The study domain this goal belongs to."
    )

    # Always store the Monday of the week for consistent querying
    week_start_date = models.DateField(
        help_text="The Monday of the week this goal is for."
    )

    target_description = models.TextField(
        help_text="What exactly do you plan to study or accomplish this week?"
    )

    target_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Total hours targeted for this goal this week (e.g. 10.5)."
    )

    is_completed = models.BooleanField(
        default=False,
        help_text="Mark True when the weekly goal has been fully achieved."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-week_start_date', 'category']
        # Enforce one goal per category per week
        unique_together = ('category', 'week_start_date')
        verbose_name = 'Weekly Goal'

    def __str__(self):
        return f"{self.category} — Week of {self.week_start_date}"

    @property
    def hours_logged(self):
        """Total hours logged across all DailyLogs for this goal."""
        result = self.daily_logs.aggregate(
            total=models.Sum('hours_spent')
        )
        return result['total'] or 0

    @property
    def progress_percentage(self):
        """Progress as a 0–100 integer, capped at 100."""
        if self.target_hours == 0:
            return 0
        pct = (self.hours_logged / self.target_hours) * 100
        return min(int(pct), 100)

    @property
    def is_on_track(self):
        """
        Simple heuristic: checks if logged hours are >= expected hours
        based on how far through the week we are (Mon=0 ... Sun=6).
        """
        today = timezone.localdate()
        days_elapsed = (today - self.week_start_date).days + 1  # 1–7
        days_elapsed = min(days_elapsed, 7)
        expected = (days_elapsed / 7) * float(self.target_hours)
        return float(self.hours_logged) >= expected


class DailyLog(models.Model):
    """
    A single end-of-day entry tied to a WeeklyGoal.
    Captures how many hours were spent and qualitative notes.
    """

    weekly_goal = models.ForeignKey(
        WeeklyGoal,
        on_delete=models.CASCADE,
        related_name='daily_logs',
        help_text="The weekly goal this log entry contributes toward."
    )

    date = models.DateField(
        default=timezone.localdate,
        help_text="The date of this log entry."
    )

    hours_spent = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        help_text="Hours actually spent on this goal today (e.g. 2.5)."
    )

    progress_notes = models.TextField(
        blank=True,
        help_text="What did you accomplish? Key concepts covered, problems solved, etc."
    )

    blockers = models.TextField(
        blank=True,
        help_text="What slowed you down? Confusion, distractions, missing resources?"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        # One log per goal per day — prevents accidental duplicates
        unique_together = ('weekly_goal', 'date')
        verbose_name = 'Daily Log'

    def __str__(self):
        return f"{self.weekly_goal.category} on {self.date} — {self.hours_spent}h"