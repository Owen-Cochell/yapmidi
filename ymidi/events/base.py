"""
Base Events to be used in ALL MIDI events!

The events outlined in this file are abstract base 
classes that are used to outline parameters and functionality
that will be used elsewhere.

IT IS NOT RECOMMENDED TO USE THESE EVENTS!

You should instead import more relevant events from elseware.
"""


class BaseEvent(object):
    """
    BaseEvent - Class all events will inherit!

    We define common attributes that all events MUST implent!
    This allows users to interact with our events in a semi-normalized way.
    We attempt to be as small and as fast as possible,
    as it is likely that many events will be loaded into memory at any given time.

    We also keep RAW MIDI data,
    which can be accessed using the 'raw' parameter.
    """

    __slots__ = ["tick", "data", "raw"]
    name = "Base MIDI Event"
    length = 0
    statusmsg = b'0x0'

    def __init__(self) -> None:
        
        self.tick = 0  # Tick this event occurs on
        self.data = None  # Data included in this event
        self.raw = b''  # RAW MIDI data associated with this event


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

    def __init__(self, channel=None) -> None:
        super().__init__()

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