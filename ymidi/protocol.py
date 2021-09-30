"""
This file defines the protocol objects to be used by yap-midi.
Protocol objects imply get data from somewhere,
be it a file, network stream, USB port, you name it!

Protocol objects have NO understanding of the MIDI specifications,
and only used to get data for the high level components.
"""


class BaseProtocol(object):
    """
    BaseProtocol - Class all sub-protocols MUST inherit!

    We define some useful functionality here,
    and provide an easy way to define protocol objects.
    Usually, the component invokes the 'get()' method
    with the requested number of bytes.
    The protocol object should then retrieve this data and return it.

    Protocol objects are meant to be ambiguous!
    They should have the freedom to do what they need to do. 
    """

    pass