import time
import logging

logger = logging.getLogger('django.request')


class RequestLoggingMiddleware:
    """
    Middleware to log incoming HTTP requests and response performance metrics.
    Logs method, path, status code, execution time, and client IP.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        # Capture client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '-')

        response = self.get_response(request)

        duration = (time.time() - start_time) * 1000  # in ms
        user = getattr(request, 'user', None)
        username = user.username if (user and user.is_authenticated) else 'anonymous'

        logger.info(
            f"[HTTP] {request.method} {request.get_full_path()} -> {response.status_code} "
            f"({duration:.2f}ms) - IP: {ip} User: {username}"
        )

        response['X-Response-Time'] = f"{duration:.2f}ms"
        return response
