import functools
import json
import cgi

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
POST_or_PUT_required = method_required('POST', 'PUT')

# Response types
def json_response(**other_data):
    """
    A parameterized decorator that returns a response in json format.
    """
    def _decorator(function):
        @functools.wraps(function)
        def _wrapper(request, *args, **kws):
            result = function(request, *args, **kws)

            # If we get a valid response, then return it unchanged.
            if isinstance(result, http.HttpResponse): return result

            # Add success code.
            if result is None: result = dict()
            if 'ok' not in result: result['ok'] = True

            # Find the status code.
            status = result.get('status')
            if status:
                del result['status']

            # Add static data.
            result.update(other_data)

            # Output the correct format.
            if request.GET.get('format') == 'html':
                # Output as debug HTML
                response = http.HttpResponse(
                    content_type="text/html",
                    status=status
                    )
                response.write(_JSONToHTML.before % request.path)
                _JSONToHTML._output(response, result)
                response.write(_JSONToHTML.after)
                return response
            else:
                json_string = json.dumps(result)
                callback = request.GET.get("callback")
                if callback is None:
                    # We have a vanilla JSON request
                    return http.HttpResponse(
                        json_string,
                        content_type="application/json",
                        status=status
                        )
                else:
                    # We have a JSONP request
                    return http.HttpResponse(
                        "%s(%s);" % (callback, json_string),
                        content_type="application/javascript",
                        status=status
                        )
        return _wrapper
    return _decorator

class _JSONToHTML(object):
    """
    This class is just used to hide its methods.
    """
    @staticmethod
    def _output(response, data):
        if isinstance(data, list):
            _JSONToHTML._output_array(response, data)
        elif isinstance(data, dict):
            _JSONToHTML._output_object(response, data)
        elif data in (True, False):
            _JSONToHTML._output_boolean(response, data)
        elif isinstance(data, basestring):
            _JSONToHTML._output_string(response, data)
        elif data is None:
            _JSONToHTML._output_null(response, data)
        else:
            _JSONToHTML._output_number(response, data)

    @staticmethod
    def _output_boolean(response, boolean):
        response.write("<div class='boolean'>%s</div>" % str(boolean).lower())

    @staticmethod
    def _output_string(response, literal):
        response.write(
            "<div class='string'>\"%s\"</div>" % cgi.escape(literal)
            )

    @staticmethod
    def _output_number(response, literal):
        response.write("<div class='number'>%s</div>" % str(literal))

    @staticmethod
    def _output_null(response, literal):
        response.write("<div class='null'>null</div>")

    @staticmethod
    def _output_object(response, obj):
        response.write("<div class='object'>")
        count = len(obj)
        if count:
            response.write("<table>")
            for key, value in sorted(obj.items()):
                response.write("<tr><th>%s:</th><td>" % cgi.escape(key))
                _JSONToHTML._output(response, value)
                response.write("</td></tr>")
            response.write("</table>")
        else:
            response.write("{}")

        response.write("</div>")

    @staticmethod
    def _output_array(response, seq):
        response.write("<div class='array'>")
        count = len(seq)
        if count:
            response.write("<table>")
            for i, item in enumerate(seq):
                response.write("<tr><th>%d</th><td>" % i)
                _JSONToHTML._output(response, item)
                response.write("</td></tr>")
            response.write("</table>")
        else:
            response.write("[]")
        response.write("</div>")

    before = """<!DOCTYPE HTML><html><head><style>
body { line-height: 16px; font-size: 14px; font-family: sans; }
table { border: 1px solid black; background-color: white; }
table tr { vertical-align: top; }
.array table tr:nth-child(odd) { background-color: #dee; }
.array table tr:nth-child(even) { background-color: #eff; }
.object table tr:nth-child(odd) { background-color: #ede; }
.object table tr:nth-child(even) { background-color: #fef; }
.boolean { color: #600; }
.string { color: #060; }
.number { color: #009; }
.number { color: #333; }
th { text-align: left; padding: 2px 10px 2px 2px; font-weight: normal; }
td { padding: 2px; }
p { margin: 0; padding: 0; font-style: italic; color: #999 }
.array th { font-style: italic; color: #999 }
</style></head><body><h1>JSON Result from: %s</h1>"""
    after = """</body></html>"""


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
