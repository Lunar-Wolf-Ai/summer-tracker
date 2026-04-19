# tracker/forms.py

from django import forms
from django.utils import timezone
from .models import WeeklyGoal, DailyLog, Category
import datetime


class WeeklyGoalForm(forms.ModelForm):
    """
    Form for creating a weekly goal.
    week_start_date is auto-set to the coming Monday — user doesn't touch it.
    """

    class Meta:
        model = WeeklyGoal
        fields = ['category', 'target_description', 'target_hours']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500',
            }),
            'target_description': forms.Textarea(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 resize-none',
                'rows': 3,
                'placeholder': 'e.g. Complete graph algorithms — BFS, DFS, Dijkstra. Solve 15 LeetCode problems.',
            }),
            'target_hours': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500',
                'min': '0.5',
                'max': '80',
                'step': '0.5',
            }),
        }

    def save(self, commit=True):
        # 2. The function body is indented 4 spaces inside the 'def'
        instance = super().save(commit=False)
        today = timezone.localdate()
        
        # Always anchor to the CURRENT week's Monday (never future)
        # today.weekday() → Mon=0, Tue=1, ... Sun=6
        instance.week_start_date = today - datetime.timedelta(days=today.weekday())
        
        if commit:
            # 3. This line is indented 4 spaces inside the 'if' statement
            instance.save()
            
        return instance


class DailyLogForm(forms.ModelForm):
    """
    End-of-day log form. Filters goals to only show the current week's active goals.
    """

    class Meta:
        model = DailyLog
        fields = ['weekly_goal', 'date', 'hours_spent', 'progress_notes', 'blockers']
        widgets = {
            'weekly_goal': forms.Select(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500',
            }),
            'date': forms.DateInput(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500',
                'type': 'date',
            }),
            'hours_spent': forms.NumberInput(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500',
                'min': '0.5',
                'max': '24',
                'step': '0.5',
            }),
            'progress_notes': forms.Textarea(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 resize-none',
                'rows': 4,
                'placeholder': 'What did you accomplish today? Topics covered, problems solved...',
            }),
            'blockers': forms.Textarea(attrs={
                'class': 'w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-indigo-500 resize-none',
                'rows': 3,
                'placeholder': 'Any blockers, confusion, or distractions? (optional)',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show goals from the current active week in the dropdown
        today = timezone.localdate()
        week_start = today - datetime.timedelta(days=today.weekday())
        self.fields['weekly_goal'].queryset = WeeklyGoal.objects.filter(
            week_start_date=week_start
        ).select_related('category')
        # Label the dropdown clearly
        self.fields['weekly_goal'].label_from_instance = lambda obj: (
            f"{obj.category.get_name_display()} — {obj.target_hours}h target"
        )
        # Default date to today
        self.fields['date'].initial = today