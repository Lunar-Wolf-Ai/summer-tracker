from django.utils import timezone

def global_context(request):
    """Injects variables available in every template automatically."""
    return {
        'today': timezone.localdate(),
    }