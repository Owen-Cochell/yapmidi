"""
IO modules for handling MIDI files.

We support reading MIDI data from an given protocol.
"""

import asyncio

from ymidi.io.base import BaseIO
from ymidi.protocol import BaseProtocol, FileProtocol
from ymidi.decoder import MetaDecoder
from ymidi.events.base import BaseEvent
from ymidi.events.builtin import StartPattern, StartTrack, StopPattern
from ymidi.constants import META, TRACK_END


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
    Otherwise, if the buffer is -1,
    then ALL events will be loaded at start time.
    
    Do note, this IO module only supports sequential event loading.
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

    def __init__(self, path: str=None, buffer: int=-1, name: str='', load_default: bool=True) -> None:

        proto = BaseProtocol()

        if path:

            # Crete a file protocol object:

            proto = FileProtocol(path)

        super().__init__(proto, MetaDecoder(), name=name)

        self.buffer = buffer  # Number of events to have loaded at one time
        self.collection = []  # Collection of objects

        self.read_check = False  # Boolean determining if the read test passed
        self.write_check = False  # Boolean determining if the write test passed

        self.num_tracks = 0  # Number of tracks present
        self.num_processed = 0  # Number of tracks processed

        self.next_event_track = True  # Boolean determining if the next event is a track header
        self.finished_processing = False  # Boolean determining if we are done processing

        # Determine if we should load the default events:

        if load_default:

            self.decoder.load_default()

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
        
        # Read the file header:

        self.collection.append(await self.read_file_header())
        
        return await super().start()

    async def get(self) -> BaseEvent:
        """
        Gets an event from the MIDI file.

        We use buffered loading, so if we need to load
        extra events then we do so here.

        :return: Event pulled from the file
        :rtype: BaseEvent
        """

        # Fill our collection if necessary:

        await self.fill_buffer()

        # Return the event at the start:

        return self.collection.pop(0)

    async def fill_buffer(self):
        """
        Fills the buffer with the necessary number of events.

        If the buffer value is 0, then we will return exactly one event.
        If the buffer value is -1, then we will load ALL midi events that we can.
        Otherwise, we ensure that the buffer is filled up to the given number.
        """

        while self.buffer < len(self.collection) + 1 and not self.finished_processing:

            # Determine if we should read the track header:

            if self.next_event_track:

                # Read the track header

                self.collection.append(await self.read_track_header())
                self.next_event_track = False

                continue

            # Otherwise, read an event:

            self.collection.append(await self.read_event())

            # Check if this track is over:

            if self.collection[-1].statusmsg == META and self.collection[-1].type == TRACK_END:

                # This track is over, make this known:

                self.next_event_track = True
                self.num_processed += 1

                # Determine if we are done processing the file:

                if self.num_tracks == self.num_processed:

                    # We are done processing, stop and return:

                    self.collection.append(StopPattern())
                    self.finished_processing = True

    async def read_track_header(self) -> StartTrack:
        """
        Reads the track chunk header at our position.
        
        We get the chunk type and length of this chunk.
        This data is used by this module to determine 
        how to parse the data in this chunk.
        
        We return a StartTrack event representing the start of this track.

        :return: StartTrack event representing the start of this track
        :rtype: StartTrack
        """
        
        # Read the chunk type(Usually MTrk):
        
        chunk_type = int.from_bytes(await self.proto.get(4))
        
        # Get the length of the chunk(Varlen):
        
        chunk_legnth = await self.read_varlen()
        
        # Return the data:
        
        return StartTrack(chunk_type, chunk_legnth)

    async def read_file_header(self) -> StartPattern:
        """
        Reads the header contaning data for this file.

        This method is usually called automatically where necessary,
        but the user can run this manually to get events.

        We return a StartPattern that represents the start of this file.

        :return: length, format, number of tracks, and divisions
        :rtype: Tuple[int, int, int, int]
        """

        # Get the ID:

        id = await self.proto.get(4)

        # Check to make sure this is a valid MIDI file:

        if id != b'MThd':

            # Not a valid file header! Do something...

            raise ValueError("Invalid file header!")

        # Get the length of the header:

        length = int.from_bytes(await self.proto.get(4), 'big')

        # Get the format of this MIDI file:

        format = int.from_bytes(await self.proto.get(2), 'big')

        # Get the number of tracks in this file:

        track_num = int.from_bytes(await self.proto.get(2), 'big')

        # Get the byte division:

        division = int.from_bytes(await self.proto.get(2), 'big')

        # Return the data:

        return StartPattern(length, format, track_num, division)

    async def read_event(self) -> BaseEvent:
        """
        Reads the next event in the file.
        
        This method is usually called automatically where necessary,
        but the user can run this manually to get events.

        :return: MIDIEvent from the file
        :rtype: BaseEvent
        """
        
        # Read the delta time:

        delta = self.decoder.read_varlen(self.proto)

        res = False
        
        while not res:
            
            # Get the result from the decoder:

            res = self.decoder.seq_decode(await self.proto.get(1))
        
        # We have our object! Attach the delta time:

        res.delta = delta

        # Finally, return the MIDI event:

        return res
