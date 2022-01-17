"""
IO modules for handling MIDI files.

We support reading MIDI data from an given protocol.
"""

import asyncio
from typing import Tuple
from ymidi.constants import START_SEQUENCE

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
    
    Do note, this IO module only support sequential event loading.
    This means that we load events in the order that they occur.
    If this is a type 0 file, then nothing should change here,
    as the events are in the order they are meant to be handled.
    However, type 1 and 2 files will have events returned out of order,
    as tracks as encountered at diffrent points in the file.
    Therefore, it is recommended to use a higher-level IO module
    for seeking and awaiting multiple tracks.
    
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

    async def start(self):
        """
        Starts the MIDI file IO module.
        
        We start by iterateing over our source file,
        and doing some sanity checks to ensure that 
        the file is valid.
        
        We also build our mapping of the MIDI file,
        so we have an understanding of the MIDI file type we are working with,
        and the number of tracks present in the MIDI file,
        if applicable.
        """
        
        # Check to see if the header chunk is present:
        
        if 'MThd' != self.proto.get(4).decode('utf-8'):
            
            # Invalid file header! Rase an exception:
            
            raise ValueError("Invalid MIDI file header!")
        
        return await super().start()

    async def get(self) -> BaseEvent:
        """
        Gets an event from the MIDI file.

        We use buffered loading, so if we need to load
        extra events then we do so here.

        :return: Event pulled from the file
        :rtype: BaseEvent
        """

        return None

    async def read_track_header(self) -> Tuple[int, int]:
        """
        Reads the track chunk header at our position.
        
        We get the chunk type and length of this chunk.
        This data is used by this module to determine 
        how to parse the data in this chunk.
        
        We return a tuple contaning the track type 
        and legnth, in that order.
        We also update our TrackInfo object with this data.
        
        :return: Track type and legnth
        :rtype: Tuple[int, int]
        """
        
        # Read the chunk type(Usually irrelevant):
        
        chunk_type = int.from_bytes(await self.proto.get(1))
        
        # Get the length of the chunk(Varlen):
        
        chunk_legnth = await self.read_varlen()
        
        # Return the data:
        
        return chunk_type, chunk_legnth

    async def read_file_header(self) -> Tuple[int, int, int, int, ]

    async def read_event(self) -> BaseEvent:
        """
        Reads the next event in the file.
        
        This method is usually called automatically where necessary,
        but the user can run this manually to get events.

        :return: MIDIEvent from the file
        :rtype: BaseEvent
        """
        
        # Read the delta time:

        delta = await self.read_varlen()

        res = False
        
        while not res:
            
            # Get the result from the decoder:
            # TODO: Fix this decoder to support meta events and special sys-exc events
            
            res = self.decoder.seq_decode(await self.proto.get(1))
        
        # We have our object! Attach the delta time:

        res.delta = delta

        # Finally, return the MIDI event:

        return res

    async def read_varlen(self) -> int:
        """
        Reads a variable length intiger.
        
        We pull values directly from the protocol object,
        so it is important to call this method where relevant!
        If you call this method, say, in the middle of an event,
        then you will likely loose the MIDI event,
        and this method will likely fail.
        
        This method is called automatically where appropriate.

        TODO: Fix this method and the write_varlen method!
        This includes testing and documentation stuff.

        :return: Intiger read
        :rtype: int
        """
        
        # Read the initial byte:
        
        value = await self.proto.get(1)
        byt = value
        
        if value & 0x80:
            
            value &= 0x7f
            
            while byt & 0x80:
                
                byt = await self.proto.get(1)
                
                value = (value << 7) + (byt & 0x7f)
                
            # Return the final value:
            
            return value

    async def write_varlen(self, num: int) -> bytes:
        """
        Converts an intiger into a collection of bytes.
        
        We return the converted bytes after the operation is complete.

        :param num: Number to encode
        :type num: int
        :return: Bytes of encoded data
        :rtype: bytes
        """
        
        buffer = num & 0x7F
        
        while True:
            
            if buffer & 0x80:
                
                buffer >>= 8
            else:
                break:
            
        return buffer
