"""
Base Events to be used in ALL MIDI events!

The events outlined in this file are abstract base 
classes that are used to outline parameters and functionality
that will be used elsewhere.

IT IS NOT RECOMMENDED TO USE THESE EVENTS!

You should instead import more relevant events from elsewhere.
"""

from ymidi.constants import META
from ymidi.misc import write_varlen


class BaseEvent(object):
    """
    BaseEvent - Class all events will inherit!

    We define common attributes that all events MUST implement!
    This allows users to interact with our events in a semi-normalized way.
    We attempt to be as small and as fast as possible,
    as it is likely that many events will be loaded into memory at any given time.

    We also keep RAW MIDI data,
    which can be accessed using the 'raw' parameter.
    This is usually attached on the decoder level,
    so this data may not always be provided!

    It is required that all events pass all parameters
    to our __init__ method.
    This allows us to keep track of the MIDI data,
    and gives us the ability to encode MIDI events in a very quick way.
    """

    __slots__ = ["tick", "data", "raw"]
    name = "Base MIDI Event"
    length: int = 0
    statusmsg: int = 0x00
    has_channel: bool = False

    def __init__(self, *args) -> None:

        self.tick = 0  # Tick this event occurs on
        self.delta = 0  # The delta time of this event in ticks
        self.data = args  # Data included in this event
        self.raw = b''  # RAW MIDI data associated with this event

        self.time = 0  # Time since the start of the track that this event occurs on in microseconds
        self.delta_time = 0  # Delta time in microseconds

    def __len__(self):
        """
        Returns the length of this event.
        """

        return len(self.data)

    def __bytes__(self) -> bytes:
        """
        Converts this event into bytes.
        
        This is mostly used by encoders,
        and is great for serialization.
        
        :return: Message in bytes
        :rtype: bytes
        """
        
        # Get the status of this message:
        
        status = self.statusmsg
        
        # Determine if we are working with channels:
        
        if self.has_channel:

            # Encode the channel number in the status message:

             status = status & 0xF0 | self.channel

        # Return the final data:

        return bytes((status,) + self.data)


class ChannelMessage(BaseEvent):
    """
    ChannelMessage - Abstract class for channel messages!

    This class is primarily used for identifying channel events,
    which usually control musical aspects in a given channel.
    For example, a NoteOn event in channel 3.

    We keep track of the channel we are registered to.
    This value is usually provided to us by some high-level component,
    but it can be manually specified as well.
    """

    __slots__ = ['channel']
    has_channel = True

    def __init__(self, *args, channel=0) -> None:
        super().__init__(*args)

        self.channel = channel


class SystemMessage(BaseEvent):
    """
    SystemMessage - Abstract class for system messages!

    This class is primarily used for identifying system events,
    which usually control meta aspects of the MIDI connection.
    For example, time synchronization messages.
    """

    pass


class SystemCommon(SystemMessage):
    """
    Base class for SystemCommon events.

    SystemCommon events are intended for all receivers in a system,
    regardless of the channel.
    They are misc. system events that don't fall into any category.
    An example of a SystemCommon event is the TuneRequest,
    which requests that all analog oscillators be tuned.
    """

    pass


class RealTimeMessage(SystemMessage):
    """
    Base class for Real Time events.

    Real time events are primarily used for clock synchronization,
    and are often times ignored by the user.
    This class can be used to identify real time messages.
    """

    length = 0
    name = "RealTimeMessage"


class BaseSystemExclusiveMessage(SystemMessage):
    """
    Base class for SystemExclusive events.
    This class has no functionality on its own,
    and is used to identify SystemExclusive messages.
    """

    name = "BaseSystemExclusive"


class BaseMetaMessage(BaseEvent):
    """
    Base class for Meta events.
    This class has no functionality on it's own,
    and is used to identify MetaEvents.
    """

    name: str = "BaseMeta"
    statusmsg = META
    type: int = 0x00  # Meta event type

    def __init__(self, *args) -> None:
        super().__init__(*args)

        self.track = 0  # Track number this event occurred on

    def __bytes__(self) -> bytes:
        """
        Converts this event into bytes.
        
        We are similar to the BaseEvent bytes method,
        except that we also encode the length and size.

        :return: Message in bytes
        :rtype: bytes
        """

        # get the length as a varlen:

        length = tuple(write_varlen(len(self.data)))

        return bytes((self.statusmsg, self.type) + length + self.data)
