from django.utils import timezone


def year(request):
    year_now = timezone.now()
    return {
        'year': year_now.year
    }
