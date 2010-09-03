import functools
import json

import django.http as http
import django.shortcuts as shortcuts
import django.template as template

# Method enforcement.
def method_required(*methods):
    """
    A parameterized decorator that requires requests to have a
    particular method.
    """
    def _decorator(function):
        @functools.wraps(function)
        def _wrapper(request, *args, **kws):
            if request.method not in methods:
                return http.HttpResponseNotAllowed(methods)
            else:
                return function(request, *args, **kws)
        return _wrapper
    return _decorator

# Specializations for particular methods.
POST_required = method_required('POST')
GET_required = method_required('GET')
PUT_required = method_required('PUT')

# Response types
def json_response(**other_data):
    """
    A parameterized decorator that returns a response in json format.
    """
    def _decorator(function):
        @functools.wraps(function)
        def _wrapper(*args, **kws):
            result = function(*args, **kws)

            # If we get a valid response, then return it unchanged.
            if isinstance(result, http.HttpResponse): return result

            # Add success code.
            if result is None: result = dict()
            if 'ok' not in result: result['ok'] = True

            # Add static data.
            result.update(other_data)

            # Output as text with the correct mime.
            json_string = json.dumps(result)
            return http.HttpResponse(
                json_string, content_type="application/json"
                )
        return _wrapper
    return _decorator

def template_response(templ, **other_data):
    """
    A parameterized decorator that returns a response passed through a
    template.
    """
    def _decorator(function):
        @functools.wraps(function)
        def _wrapper(request, *args, **kws):
            result = function(request, *args, **kws)

            # If we get a valid response, then return it unchanged.
            if isinstance(result, http.HttpResponse): return result

            # Add static data.
            result.update(other_data)

            # Render to a template and return.
            return shortcuts.render_to_response(
                templ, result,
                context_instance=template.RequestContext(request)
                )
        return _wrapper
    return _decorator
