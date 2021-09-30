"""
This file defines decoder objects for yap-midi.

A 'decoder' takes data in a certain format,
and converts said data into a valid MIDI instance.
This is probably not surprising to you,
but you may be interested to hear that decoders
also encode MIDI instances back into the data in the original format!
Neato!

These classes are usually used by IO classes,
but you can use these standalone if you wish.
"""


class BaseDecoder(object):
    """
    BaseDecoder - Class all decoders MUST inherit!

    We define some functionality all decoders must implement.
    We also try to keep decoder implementation ambiguous,
    as decoders can work with pretty much anything!
    """

    pass