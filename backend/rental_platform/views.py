from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET

@require_GET
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    This view simply returns a CSRF token cookie to the client.
    The @ensure_csrf_cookie decorator ensures that a CSRF cookie is set.
    This CSRF cookie is then used for all subsequent POST, PUT, PATCH, or DELETE requests.
    """
    return JsonResponse({'detail': 'CSRF cookie set'}) 