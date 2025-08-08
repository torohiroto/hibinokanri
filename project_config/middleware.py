import base64
import os
from django.http import HttpResponse

class BasicAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow admin access without auth
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        auth_user = os.environ.get('BASIC_AUTH_USER')
        auth_pass = os.environ.get('BASIC_AUTH_PASSWORD')

        # If credentials are not set in environment, skip auth
        if not auth_user or not auth_pass:
            return self.get_response(request)

        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                try:
                    auth_bytes = auth[1].encode('utf-8')
                    decoded_auth = base64.b64decode(auth_bytes).decode('utf-8')
                    username, password = decoded_auth.split(':', 1)
                    if username == auth_user and password == auth_pass:
                        return self.get_response(request)
                except (ValueError, TypeError):
                    pass

        # If authentication fails, send a 401 response
        response = HttpResponse("Unauthorized", status=401)
        response['WWW-Authenticate'] = 'Basic realm="Restricted Area"'
        return response
