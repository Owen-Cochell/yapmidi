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

    async def read(self, byts: int) -> bytes:
        """
        Reads a given amount of bytes.

        :param byts: Number of bytes to read
        :type byts: int
        :return: Bytes read
        :rtype: bytes
        """

        pass

    async def write(self, byts: bytes) -> int:
        """
        Writes the given bytes.

        :param byts: Bytes to write
        :type byts: bytes
        :return: Number of bytes written
        :rtype: int
        """

        pass

    def start(self):
        """
        Starts this Protocol object.
        
        This object should do startup stuff here
        that prepares it for use.
        """
        
        pass

    def stop(self):
        """
        Stops this Protocol object.
        
        The object can safely assume that it will not
        be called again until the start method is called.
        """
        
        pass
