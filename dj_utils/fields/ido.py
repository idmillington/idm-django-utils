import random

from django.db import models
import django.dispatch as dispatcher

class IdObfuscator(object):
    """
    A utility class that implements an n-bit mixing algorithm which
    can turn positive integers into short-codes.

    This is used in many applications where objects need a unique id,
    which is short and can be derived from an auto-incrementing
    integer. It is well-known from link-shorteninig services such as
    bit.ly or Youtube video identifiers.
    """

    # We use a custom base32 encoding designed to remove any ambiguous
    # letters/numbers, so the resulting id is as easy to type as
    # possible.
    DEFAULT_CODE_CHARS = "abcdefghijkmnpqrstuvwxyz23456789"

    @staticmethod
    def create_from_seed(bits, seed=None):
        """
        Builds an obfuscator with a random set of base xor values,
        generated from the given seed.

        Bits should be an integer giving the number of bits of value
        to support, so 32 would give an obfuscator capable that will
        generate 2**32 ids before colliding.

        The seed should be any hashable object (as required by the
        random.seed method of the standard library). If no seed is
        given, then the current time is used, but this isn't normally
        useful, because the aim of this class is to be consistent over
        long periods of time. It is primarily intended for testing.
        """
        # Initialise our random number generator
        rnd = random.Random()
        rnd.seed(seed)

        # Create random integers with successively higher number of
        # digits, and always with a 1 in the most significant bit. We
        # do this so that we guarantee that no xor is a linear
        # combination of others (i.e. the xor matrix is non-singular),
        # and therefore there can't be any collisions.
        xor_temp = [
            (1 << i) + rnd.randint(0, (1 << i) - 1)
            for i in range(bits+1)
            ]

        # Consistently shuffle the bits in the xors we came up with.
        xors = []
        mapping = range(bits)
        rnd.shuffle(mapping)
        for x in xor_temp:
            v = 0
            for i in range(bits):
                if x & (1 << i): v += (1 << mapping[i])
            xors.append(v)

        # We reverse this so that, on average, small changes on input
        # have the maximal effect on output. We could shuffle here,
        # which would distribute the size of changes over the size of
        # inputs, but when we are dealing with incrementing values,
        # this is a better solution.
        xors.reverse()
        ido = IdObfuscator(xors)
        ido.seed = seed
        return ido

    def __init__(self, xors, code_chars=None):
        """
        Creates a new obfuscator from the given set of xor data.

        There should be one more xor than the number of bits in the
        largest id we're planning to encode.
        """
        self.xors = xors
        self.bits = len(xors)-1

        self.code_chars = code_chars or IdObfuscator.DEFAULT_CODE_CHARS
        assert len(self.code_chars) == 32, "Must have 32 code characters."

        # Masks to check single bits in the input with: value & masks[bit]
        self.masks = [1 << i for i in range(self.bits)]

    def get_obfuscated_id_value(self, raw_value):
        """
        Returns the obfuscated id corresponding to the given raw
        numeric value, as a numeric value itself.
        """
        result = self.xors[-1]
        for mask, xor in zip(self.masks, self.xors):
            if raw_value & mask:
                result ^= xor
        return result

    def get_obfuscated_id(self, raw_value):
        """
        Returns the obfuscated id as a custom base32-encoded string.
        """
        code_chars = self.code_chars

        # Do a simple base 32 encoding, without any padding characters.
        r = []
        value = self.get_obfuscated_id_value(raw_value)
        for i in range((self.bits+4) // 5):
            r.append(code_chars[value % 32])
            value >>= 5
        return "".join(reversed(r))

class ObfuscatedIdField(models.CharField):
    """
    A field that provides obfuscated id support to Django models.

    As well as the standard Django field parameters, this field requires:

    'bits' - The maximum number of bits that should be
             supported. After this number of bits, the obfuscated ids
             will repeat. Because of the way the final codes are
             base32 encoded, there is no space saving to using
             anything other than numbers of bits divisible by 5. So if
             you really only need 32-bits, you may as well specify
             35. There is a slight time penalty to this, but it is
             highly marginal.

    'seed' - A hashable object that makes each obfuscated id field
             follow a different sequence. The best thing to use here is
             a hard-coded UUID string, e.g.
             "333cd3bc-7fd9-4310-93c2-e906c9b7b269"

    And optionally:

    'source_field' - The obfuscated id works by translating a positive
                     integer field into the obfuscated id
                     short-code. This parameter controls which
                     positive integer field should be used. If none is
                     given then the system assumes that the
                     Django-default 'id' field is in use.
    """
    def __init__(self, *args, **kws):
        name = self.__class__.__name__
        bits = kws['bits']
        self.source_field = kws.get('source_field', 'id')
        self.ido = IdObfuscator.create_from_seed(bits, kws['seed'])
        if 'code_chars' in kws:
            chars = kws['code_chars']
            assert len(chars) == 32, "Must have 32 characters for encoding."
            self.ido.code_chars = chars

        # Force certain CharField properties.
        max_length = int((bits+4)//5)
        kws['max_length'] = max_length
        kws['editable'] = False
        kws['null'] = True # When saving a new object, we use null as a temp.

        # Optional others
        kws.setdefault('db_index', True)

        # Remove any keywords that would confuse the base class.
        del kws['bits']
        del kws['seed']
        if 'source_field' in kws: del kws['source_field']
        if 'code_chars' in kws: del kws['code_chars']

        # Delegate to create the field.
        models.CharField.__init__(self, *args, **kws)

    def contribute_to_class(self, cls, name):
        """
        We register against save signals, so that when this class
        tries to save, we can update its oid fields.
        """
        models.signals.pre_save.connect(self._pre_save, sender=cls)
        models.signals.post_save.connect(self._post_save, sender=cls)
        super(ObfuscatedIdField, self).contribute_to_class(cls, name)

    def _pre_save(self, sender, instance, using=None, *args, **kws):
        """
        Update this field, if possible, based on the value of the
        source field.

        If we don't have a value for the source field (this is the
        case when the source is the auto-incrementing id field and we
        are saving for the first time), then we'll need to wait until
        after the instance is saved.
        """
        source_val = getattr(instance, self.source_field)
        if source_val:
            oid = self.ido.get_obfuscated_id(source_val)
            setattr(instance, self.name, oid)
        else:
            # Use null as a temporary oid, we'll create the real one
            # post-save.
            setattr(instance, self.name, None)

    def _post_save(self, sender, instance, *args, **kws):
        """
        Update this field, if we didn't do it in pre_save.
        """
        if kws.get('created'):
            # Make sure we have a source field now.
            source_val = getattr(instance, self.source_field)
            assert source_val, _(
                "The source field '%s' was never set, "
                "could not create an obfuscated it" % self.source_field
                )

            # Create the oid.
            oid = self.ido.get_obfuscated_id(source_val)
            setattr(instance, self.name, oid)

            # Do another save to save the oid.
            instance.save(using=kws.get('using'))


# If we're using south for schema migration, then register this field.
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(
        [(
                [ObfuscatedIdField],
                [],
                {
                    "seed": ("ido.seed", {}),
                    "bits": ("ido.bits", {}),
                    "source_field": ("source_field", {"default":"id"})
                }
        )],
        ["^dj_utils\.fields\.ido\.ObfuscatedIdField"]
        )
except ImportError:
    pass
