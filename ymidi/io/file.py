"""
IO modules for handling MIDI files.

We support reading MIDI data from an given protocol.
"""

import asyncio

from ymidi.io.base import BaseIO
from ymidi.protocol import BaseProtocol
from ymidi.decoder import ModularDecoder
from ymidi.events.base import BaseEvent


class MIDIFile(BaseIO):
    """
    MIDIFile - Allows content to be read and written in MIDI format.

    We support reading and writing MIDI data,
    including special events such as meta events.

    We support full loading all MIDI events into memory at start time,
    which will allows events to be accessed quickly but requires more memory.
    This is the default operation.

    We also support partial event loading where we only pull
    events from our source when necessary,
    which uses less memory overall but also causes latency when loading the file.
    This can be enabled by using the 'buffer' parameter,
    which determines how many events to load at a time.
    If you want to load an event each time one is requested,
    then you would pass 0 to this parameter.
    
    Like other IO modules, we support attaching a custom protocol
    object that reads data from anywhere.
    Most people will want to read content from a file,
    so by default we will create a FileProtocol object.
    """

    NAME = "MIDIFile"

    def __init__(self, path:str='', buffer: int=None, name: str='') -> None:

        super().__init__(BaseProtocol(), ModularDecoder(), name=name)

        self.buffer = buffer  # Number of events to have loaded at one time
        self.collection = []  # Collection of objects

        self.read_check = False  # Boolean determining if the read test passed
        self.write_check = False  # Boolean determining if the write test passed

    def get(self) -> BaseEvent:
        """
        Gets an event from the MIDI file.

        We use buffered loading, so if we need to load
        extra events then we do so here.

        :return: Event pulled from the file
        :rtype: BaseEvent
        """

        return None

