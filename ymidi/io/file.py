"""
IO modules for handling MIDI files.

We support reading MIDI data from an given protocol.
"""

import asyncio
import struct

from ymidi.io.base import BaseIO
from ymidi.protocol import BaseProtocol, FileProtocol
from ymidi.decoder import MetaDecoder
from ymidi.events.base import BaseEvent
from ymidi.events.meta import EndOfTrack
from ymidi.events.builtin import StartPattern, StartTrack, StopPattern
from ymidi.constants import META, TRACK_END
from ymidi.misc import write_varlen


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
    then you would pass 1 to this parameter.
    Otherwise, if the buffer is 0,
    then ALL events will be loaded at start time.

    Do note, this IO module only supports sequential event loading.
    This means that we load events in the order that they occur.
    If this is a type 0 file, then nothing should change here,
    as the events are in the order they are meant to be handled.
    However, type 1 and 2 files will have events returned out of order,
    as tracks as encountered at different points in the file.
    Therefore, it is recommended to use a higher-level IO module
    for seeking and awaiting multiple tracks.

    Like other IO modules, we support attaching a custom protocol
    object that reads data from anywhere.
    Most people will want to read content from a file,
    so by default we will create a FileProtocol object.
    """

    NAME = "MIDIFile"

    def __init__(self, path: str=None, buffer: int=0, name: str='', load_default: bool=True) -> None:

        proto = BaseProtocol()

        if path:

            # Crete a file protocol object:

            proto = FileProtocol(path)

        super().__init__(proto, MetaDecoder(), name=name)

        self.buffer = buffer  # Number of events to have loaded at one time
        self.collection = asyncio.Queue()  # Queue of events

        self.num_tracks = 0  # Number of tracks present
        self.num_processed = 0  # Number of tracks processed

        self.next_event_track = True  # Boolean determining if the next event is a track header
        self.finished_processing = False  # Boolean determining if we are done processing

        self.file_header = False  # Determines if we wrote the file header
        self.writing_track = False  # Determines if we are currently writing a track

        # Determine if we should load the default events:

        if load_default:

            self.decoder.load_default()

    async def start(self):
        """
        Starts the MIDI file IO module.

        We start by iterating over our source file,
        and doing some sanity checks to ensure that 
        the file is valid.

        We also build our mapping of the MIDI file,
        so we have an understanding of the MIDI file type we are working with,
        and the number of tracks present in the MIDI file,
        if applicable.
        """

        # Read the file header:

        await self.collection.put(await self.read_file_header())

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

        return await self.collection.get()

    async def put(self, event: BaseEvent):
        """
        Writes the given event to the MIDI file.
        
        :param event: Event to write
        :type event: BaseEvent
        """

        # Determine if this is a StartPattern:

        if not self.file_header and isinstance(event, StartPattern):

            # Write the file header:

            await self.write_file_header(event.length, event.format, event.num_tracks, event.divisions)

            self.file_header = True

            return

        # Determine if we should write a track header:

        if not self.writing_track and isinstance(event, StartTrack):

            # Write the track header:

            await self.write_track_header(event.chunk_type, event.length)

            self.writing_track = True

            return

        # Determine if this track is over:

        if self.writing_track and isinstance(event, EndOfTrack):

            # End this track:

            self.writing_track = False

        # Finally, write the event:

        self.write_event(event)

    def has_events(self) -> bool:
        """
        Determines if we have any more events to process.
        
        We first check to see if there are more events available to be processed.
        If not, then we check if we have any events in the queue.
        
        We return True if there are events to be returned,
        and False if there are no more events to return.

        :return: Boolean determining if there are more events to return
        :rtype: bool
        """
        
        # Check if we have more to process:
        
        if self.finished_processing:
            
           # Check if there are events in the queue:
           
           if self.collection.empty():
               
               # No more events, return False:
               
               return False

        # Return True:

        return True

    async def fill_buffer(self):
        """
        Fills the buffer with the necessary number of events.

        If the buffer value is 0, then we will load ALL midi events that we can.
        Otherwise, we ensure that the buffer is filled up to the given number.
        """

        while (not self.buffer or self.buffer > self.collection.qsize()) and not self.finished_processing:

            # Determine if we should read the track header:

            if self.next_event_track:

                # Read the track header

                await self.collection.put(await self.read_track_header())
                self.next_event_track = False

                continue

            # Otherwise, read an event:

            event = await self.read_event()

            await self.collection.put(event)

            # Check if this track is over:

            #print(self.collection[-1])

            if event.statusmsg == META and event.type == TRACK_END:

                # This track is over, make this known:

                print("Track complete!")

                self.next_event_track = True
                self.num_processed += 1

                print("Number of tracks processed: {}".format(self.num_processed))
                print("Number of tracks present: {}".format(self.num_tracks))

                # Determine if we are done processing the file:

                if self.num_tracks == self.num_processed:

                    # We are done processing, stop and return:

                    await self.collection.put(StopPattern())
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

        # Read in header data:

        data = struct.unpack('>4sL', await self.proto.read(8))

        # Return the data:

        return StartTrack(data[0], data[1])

    async def read_file_header(self) -> StartPattern:
        """
        Reads the header containing data for this file.

        This method is usually called automatically where necessary,
        but the user can run this manually to get events.

        We return a StartPattern that represents the start of this file.

        :return: length, format, number of tracks, and divisions
        :rtype: Tuple[int, int, int, int]
        """

        # Get the ID:

        id = await self.proto.read(4)

        # Check to make sure this is a valid MIDI file:

        if id != b'MThd':

            # Not a valid file header! Do something...

            raise ValueError("Invalid file header!")

        # Get the length of the header:

        length = int.from_bytes(await self.proto.read(4), 'big')

        # Get the format of this MIDI file:

        format = int.from_bytes(await self.proto.read(2), 'big')

        # Get the number of tracks in this file:

        self.num_tracks = int.from_bytes(await self.proto.read(2), 'big')

        # Get the byte division:

        division = int.from_bytes(await self.proto.read(2), 'big')

        # Return the data:

        return StartPattern(length, format, self.num_tracks, division)

    async def read_event(self) -> BaseEvent:
        """
        Reads the next event in the file.
        
        This method is usually called automatically where necessary,
        but the user can run this manually to get events.

        :return: MIDIEvent from the file
        :rtype: BaseEvent
        """

        # Read the delta time:

        delta, read = self.decoder.read_varlen(self.proto)

        print("Delta time: {} ; Items read: {}".format(delta, read))

        res = None
        
        while res is None:
            
            # Get the result from the decoder:

            res = self.decoder.seq_decode(await self.proto.read(1))
        
        # We have our object! Attach the delta time:

        res.delta = delta

        # Attach the track number:
        
        res.track = self.num_processed

        # Finally, return the MIDI event:

        print("Processed event: {}".format(res))

        return res

    async def write_track_header(self, track_type:str, length: int) -> int:
        """
        Writes the track header with the given values.

        :param track_type: Type of track to write, usually 'MTrk'
        :type track_type: str
        :param length: Length 
        :return: Number of bytes written
        :rtype: int
        """

        # Get and return the data:

        return await self.proto.write(struct.pack('>4sL', bytes(track_type, encoding='ascii'), length))

    async def write_file_header(self, length:int, format:int, num_tracks: int, byte_div: int) -> int:
        """
        Writes the file header using the given values.

        :param length: Length of this header
        :type length: int
        :param format: Format of this file, should be 0, 1, 2
        :type format: int
        :param num_tracks: Number of tracks in this file
        :type num_tracks: int
        :param byte_div: Byte division of this file
        :type byte_div: int
        :return: Number of bytes written
        :rtype: int
        """

        # Encode header text:

        data = bytes('MThd', encoding='ascii')

        # Encode the varlen:

        data += write_varlen(length)

        # Encode the number of tracks:

        data += struct.pack(">3h", format, num_tracks, byte_div)

        # Write the data:

        self.proto.write(data)

    async def write_event(self, event: BaseEvent):
        """
        Writes an event to the protocol object.

        :param event: Event to write
        :type event: BaseEvent
        """

        # Write the data:

        self.proto.write(self.decoder.encode(event))
