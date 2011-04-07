# Django Utilities

This is my collection of useful decorators and field types for my
Django projects. It is completely idiosyncratic to the kinds of
project I work on.

## Choices

Django uses a sequence of tuples for its 'choices' values, which are
basically enumerated objects. The choices module has a more
comprehensive class that allows you to associate more data (such as
description strings) with choices, and allows you to refer to values
by name. For example, we can do:

    PRIVACY_CHOICES = choices.Choices(
        (0, 'PRIVATE', _('Private')),
        (1, 'FRIENDS', _('Show friends')),
        (2, 'PUBLIC', _('Show everyone'))
        )

and then

    photo.privacy = PRIVACY_CHOICES.PRIVATE


## Decorators

The decorators replace some of the simple templating function calls in
Django, in a way that makes it simple to create JSON-based
web-services.

### `template_response`

For basic HTML templates you can add the `template_response` decorator
to a view, and just return the context dictionary:

    @template_response('photos/photo.html')
    def view_photo(request, photo_id):
        photo = get_object_or_404(models.Photo, pk=photo_id)
        if not photo.visible_to(request.user):
            return http.HttpResponseForbidden()
        return dict(photo=photo)

Notice that if your view returns a `HttpResponse` subclass, rather
than a dictionary (in the example a `HttpResponseForbidden`), the
decorator will pass that response right through.

The `template_response` decorator will render the template using a
`RequestContext` (i.e. it will include any context processors).

### `json_response`

There is a similar decorator for JSON responses. You return a
dictionary again, and it returns the data in the dictionary as
json-encoded with the json mime-type.

    @json_response()
    def view_photo(request, photo_id):
        photo = get_object_or_404(models.Photo, pk=photo_id)
        if not photo.visible_to(request.user):
            return http.HttpResponseForbidden()
        return dict(photo=photo)

The `json_response` decorator supports two query
parameters. `format=html` outputs the json response in a HTML page,
for debugging. Where `callback` provides normal jsonp support.

Because of the way I design my webservice APIs, the decorator adds
`ok=True` to the top level json object, if `ok` isn't otherwise set.

Finally, you can set `status` in the dictionary you send to the
decorator to change the http status of the return from 200. This means
you can send json webservice responses for HTTP error conditions.

### `method_required`

While we're talking webservices, there is a `method_required`
decorator that prevents access to a view if one of the given HTTP
methods isn't being used. We do

    @method_required('POST')
    def reset_counter():
        ...

There are convenience versions for `POST_required`, `GET_required`,
`PUT_required` and `POST_or_PUT_required`.


### `report_errors`

A few times while debugging Ajax responses, I've found that when
something dies in debug mode, the fancy django error message is
useless (because the script that is calling the view is expecting a
JSON response). This decorator outputs the traceback to stdout for
debugging, as a basic way of finding errors. This decorator is a no-op
unless django is in debug mode.


## Fields

There are a bunch of useful fields defined in the `fields` package.

### Obfuscated ID

If you want short-codes that are difficult to guess, then the
`ObfuscatedIdField` is a mixing function that turns the
auto-incrementing primary key of a model into an encoded string. You
give it a number of bits (normally 35 for a full 32-bit integer
precision, smaller if you want the code to be smaller), and it stores
and indexes the resulting id.

### JSON and Pickle fields

These are two ways to store arbitrary data structures in Django. Both
provide automatic deserialization and serialization.

### Password field

This replicates much of the machinery of the password field used in
the `django.contrib.auth` module. It provides salt, and a configurable
hashing algorithm, to avoid storing passwords in plaintext.

### Slug field

The default django slug is a little too general for my taste. Its
ability to use upper and lower case text means you can have ids that
vary only in case, and the use of underscore and hyphen are similarly
error-prone. My slug field uses a stricter format with only ASCII
lowercase a-z, 0-9 and hyphens. The slug must start with a letter, it
may neither end with a hyphen nor have more tha one hyphen
consecutively within it. So `foo-bar` is valid, but `foo-bar-` and
`foo--bar` are not.

### UUID field

A very simple field that holds an ISO UUID. It uses a random version 4
uuid as its default value, but you can define the default for the
field as normal to override this.


## Settings Utils

The final module allows me to use one config file for settings for a
bunch of different developers, while being able to commit those
settings to the repo. I.e. without using `local_settings`. I do use
`local_settings`, but only for data that shouldn't be in the repo.

The `settings_utils` module is imported into the `settings.py` file,
and settings that change are marked as:

    MEDIA_ROOT = config(
        'media',
        ian_linux = '/home/ian/data/django/example/media',
        bob_mac = '/Users/bob/Documents/Django/example/media'
        )

where the keyword arguments are the settings for different users, and
the single positional argument is the default setting.

You control which setting you want by placing a `.machine_id` file in
the same directory as `settings.py` or by defining a
`DJANGO_MACHINE_ID` environment variable. The file or environment
variable should contain the name of your machine, e.g.

    $ export DJANGO_MACHINE_ID=ian_linux

or

    $ echo "bob_mac" > .machine_id

This approach is particularly useful when you have common derived
settings, and want varation in the settings they rely on. For example
I usually do something like:

    ROOT = os.path.abspath(os.path.dirname(__file__))

in my `settings.py` file, and then do stuff like

    MEDIA_ROOT = os.path.join(ROOT, 'media')

This would be harder to do without duplicating the `MEDIA_ROOT`
setting in `local_settings`, but is simple with the `config` approach.