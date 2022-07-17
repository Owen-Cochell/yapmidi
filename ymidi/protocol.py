"""
This file defines the protocol objects to be used by yap-midi.
Protocol objects imply get data from somewhere,
be it a file, network stream, USB port, you name it!

Protocol objects have NO understanding of the MIDI specifications,
and only used to get data for the high level components.
"""

from __future__ import annotations

import asyncio


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

    def sync_read(self, byts: int) -> bytes:
        """
        A synchronous implementation of this protocol object.

        By default, we simply run the coroutine in the event loop,
        so we get a synchronous-like adaptation.
        Protocol objects can override this method and implement
        their own functionality that may be faster then the default.

        :param byts: Number of bytes to read
        :type byts: int
        :return: Bytes read
        :rtype: bytes
        """

        return asyncio.get_event_loop().run_until_complete(self.read(byts))

    def sync_write(self, byts: bytes) -> int:
        """
        A synchronous implementation of this protocol object.

        By default, we simply run the coroutine in the event,
        so we get a synchronous-like adaptation.
        Protocol objects can override this method and implement
        their own functionality that may be faster than the default.

        :param bytes: Bytes to write
        :type bytes: bytes
        :return: Number of bytes written
        :rtype: int
        """

        return asyncio.get_event_loop().run_until_complete(self.write(byts))

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

    def __iter__(self) -> BaseProtocol:
        """
        Returns this object for iteration.

        :return: This object
        :rtype: BaseProtocol
        """

        return self

    def __next__(self) -> bytes:
        """
        Returns the next byte to be read.

        Because for loops are synchronous,
        we call the synchronous read method.

        :return: Byte read
        :rtype: bytes
        """

        return self.sync_read(1)[0]


class FileProtocol(BaseProtocol):
    """
    FileProtocol - Reads data from a file on the operating system.

    Because file operations are NOT asynchronous,
    we utilize executers to emulate asynchronous activity.

    We read bytes by default. Users can open the file in write mode
    by passing True to the 'write' parameter.

    By default, we read and write all data as bytes.
    Users can define a custom mode if they so choose.

    TODO: Figure this out, threading overhead is insane, maybe default to BLockingFileProtocol?
    """

    def __init__(self, path: str, write: bool=False, extra: str='b') -> None:

        super().__init__()

        self.path = path  # Path to the file to read
        self.opener = open(path, ("w" if write else "r") + extra)
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

        return await asyncio.to_thread(self.opener.write, byts)

    def sync_read(self, byts: int) -> bytes:
        """
        Reads the given bytes from a file synchronously.

        :param byts: Bytes to read
        :type byts: int
        :return: Bytes read
        :rtype: bytes
        """

        # Read from file and return:

        return self.opener.read(byts)

    def sync_write(self, byts: bytes) -> int:
        """
        Writes the given bytes to a file synchronously.

        :param byts: Bytes to write
        :type byts: bytes
        :return: Number of bytes written
        :rtype: int
        """

        # Write to file and return:

        return self.opener.write(byts)


class BlockingFileProtocol(FileProtocol):
    """
    BlockingFileProtocol - Reads data from a file on the operating system.

    We are identical to the FileProtocol,
    except that we don't use threads to emulate asynchronous behavior.
    This object will block the event loop while reading/writing.

    This means that the event loop will be unable to
    process other tasks while this object is active.
    However, this object is *much* faster than FileProtocol,
    as it doesn't use threads.
    """

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

        return self.opener.read(byts)

    async def write(self, byts: int) -> int:
        """
        Writes the given bytes to a file.

        If this file is not opened in write mode,
        then an exception will be raised.

        We return the number of bytes written.

        :param byts: Bytes to write
        :type byts: int
        :return: Number of bytes written
        :rtype: int
        """

        return self.opener.write(byts)
