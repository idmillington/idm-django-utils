import collections

class Choices(object):
    """
    A class that can act as a set of choices for a Django model, but
    is also useful as an enumerated type.
    """
    def __init__(self, *choice_data, **kws):
        """
        Creates the choices with quads of (value, attr_name,
        readable_string, extra_data). Where extra_data is an optional
        dictionary of other named properties of each choice.

        The following keyword arguments are acceptable:

        * 'inherit' - an existing choices instance to extend. The
          additional choice data are combined with the inherited
          data.

        * 'sort' - if inheritance is given, and sort is True, the
          inherited choices and the new choices will be sorted into
          ascending order. This is used so that the choices display in
          the correct order in ChoiceField instances. The default is
          sort=True, so set sort=False to disable this behavior.
        """
        # Check if we need to inherit from an existing set of choices.
        if 'inherit' in kws:
            other_choice = kws['inherit']
            del kws['inherit']

            # Extend the inherited data.
            choice_data = other_choice._choice_data + choice_data

            # Check if we need to sort.
            sort = True
            if 'sort' in kws:
                sort = kws['sort']
                del kws['sort']
            if sort:
                choice_data = sorted(choice_data)

        # Any other keyword argument we ignore.
        if kws:
            raise ArgumentError(
                "No such keyword argument: '%s'" % kws.keys()[0]
                )

        self._choice_data = choice_data

        # The Django choices sequence.
        self._choices = [(trip[0], trip[2]) for trip in choice_data]

        # Mappings for looking up various combinations of data.
        self._name2val = dict([(trip[1], trip[0]) for trip in choice_data])
        self._val2str = dict([(trip[0], trip[2]) for trip in choice_data])

        # Additional data.
        self._val2data = dict()
        self._data2val = collections.defaultdict(dict)
        for trip in choice_data:
            if len(trip) > 3:
                self._val2data[trip[0]] = trip[3]
                for key, val in trip[3].items():
                    self._data2val[key][val] = trip[0]
            else:
                self._val2data[trip[0]] = dict()

    def __len__(self):
        """
        Returns the number of choices.
        """
        return len(self._choices)

    def __iter__(self):
        """
        Returns the iterator over the choices. This method allows
        instances of this class to be used as the choices= parameter
        of django fields.
        """
        return iter(self._choices)

    def __getattr__(self, name):
        """
        Returns the value associated with the given name. This allows
        us to write things of the form MY_CHOICES.MY_VALUE.
        """
        try:
            return self._name2val[name]
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, value):
        """
        Returns the string associated with the given value.
        """
        return self.value_to_string(value)

    def value_to_string(self, value):
        """
        Returns the string from the given value.
        """
        return self._val2str[value]

    def value_to_data(self, value, data_type, default=None):
        """
        Returns a piece of additional data for the given data.
        """
        return self._val2data[value].get(data_type, default)

    def data_to_value(self, data_type, data_value, default=None):
        """
        Returns the value for a piece of additional data.
        """
        return self._data2val[data_type].get(data_value, default)
