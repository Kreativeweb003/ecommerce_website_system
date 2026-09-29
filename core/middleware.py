from django.http import HttpResponse, JsonResponse
from django_ratelimit.exceptions import Ratelimited
from .utils import is_ajax
import time
import logging

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    """Logs slow requests — useful once the dashboard/product-list queries grow in complexity."""

    SLOW_REQUEST_THRESHOLD_SECONDS = 1.0

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()
        response = self.get_response(request)
        duration = time.monotonic() - start_time

        if duration > self.SLOW_REQUEST_THRESHOLD_SECONDS:
            logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}s")

        return response




class RatelimitMiddleware:
    """Catches Ratelimited exceptions raised anywhere in the request and returns a proper 429."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, Ratelimited):
            message = "Too many requests. Please wait a moment and try again."
            if is_ajax(request):
                return JsonResponse({"success": False, "error": message}, status=429)
            return HttpResponse(message, status=429, content_type="text/plain")
        return None





  