import os, sys

_id = None
def environment():
    """Returns the machine id that this install is running on."""
    global _id
    if _id is None:
        if 'DJANGO_MACHINE_ID' in os.environ:
            _id = os.environ['DJANGO_MACHINE_ID']
        else:
            # Look in the current directory, then the user's home,
            # then the python path.
            paths = [".", os.path.expanduser("~")] + sys.path
            for path in paths:
                fn = os.path.join(path, '.machine_id')
                if os.path.isfile(fn):
                    _id = open(fn).read().strip()
                    break
            else:
                _id = 'development'
                import textwrap
                print '\n'.join(textwrap.wrap(textwrap.dedent("""
                    Running as development server with machine id
                    '%s'. You should set this explicitly. The best way
                    is to set the DJANGO_MACHINE_ID environment
                    variable (e.g. in the WSGI, shell or mod_python
                    configuration). Alternatively create a file called
                    '.machine_id' containing just the id. The
                    '.machine_id' file can go in the CWD, in your home
                    directory, or in sys.path: the environment
                    variable setting takes priority, then the paths
                    are searched in that order.
                    """ % _id), 76))
    return _id

def config(default=None, environment=environment(), **values):
    """Pick a specific configuration value for a specific environment."""
    if environment in values:
        return values[environment]
    else:
        return default
