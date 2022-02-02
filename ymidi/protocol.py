"""
This file defines the protocol objects to be used by yap-midi.
Protocol objects imply get data from somewhere,
be it a file, network stream, USB port, you name it!

Protocol objects have NO understanding of the MIDI specifications,
and only used to get data for the high level components.
"""

import asyncio

from numpy import byte


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


class FileProtocol(BaseProtocol):
    """
    FileProtocol - Reads data from a file on the operating system.

    Because file operations are NOT asynchronous,
    use utilise executers to emulate asynchronous activity.

    We read bytes by default. Users can open the file in write mode
    by passing True to the 'write' parameter.

    By default, we read and write all data as bytes.
    Users can define a custom mode if they so choose.
    """

    def __init__(self, path: str, write: bool=False, extra: str='b') -> None:

        super().__init__()

        self.path = path  # Path to the file to read
        self.opener = open(path, ("b" if write else "r") + extra)
        self.loop = asyncio.get_event_loop()

    async def read(self, byts: int) -> bytes:
        """
        Reads the given number of bytes from the file.

        If the file is not opened in read mode,
        then an exception will be raised.

        We return the bytes read from the file.

        :param byts: Number of bytes to read
        :type byts: int
        :return: Bytes read from the file.
        :rtype: bytes
        """

        return await asyncio.to_thread(self.opener.read, byts)

    async def write(self, byts: bytes) -> int:
        """
        Writes the given bytes to a file.

        If the file is not opened in write mode,
        then an exception is raised.

        We return the number of bytes written.

        :param byts: Bytes to write
        :type byts: bytes
        :return: Number of bytes written
        :rtype: int
        """

        return await asyncio.to_thread(self.opener, byts)
