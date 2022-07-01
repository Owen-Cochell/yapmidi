"""
These events are built into yap-midi.
These events do NOT represent valid MIDI info,
and are instead used to represent things relevant only for yap-midi,
such as start of files and tracks, and end of MIDI files.

ALL builtin events have negative status messages.
"""

from ymidi.events.base import BaseEvent


class StartPattern(BaseEvent):
    """
    StartPattern - Represents the start of a MIDI pattern,
    which is a collection of tracks.
    This builtin event is usually generated when MIDI info is being played back.
    For example, MIDI file IO modules will generate these events.

    This event contains info about the given pattern,
    which entails the format and divisions.
    """

    name: str = "StartPattern"
    statusmsg: int = -1

    def __init__(self, length, format, num_tracks, divisions) -> None:

        super().__init__(length, format, num_tracks, divisions)

        self.length = length  # Length of the pattern header
        self.format = format  # Format of this pattern
        self.num_tracks = num_tracks  # Number of tracks in this pattern
        self.divisions = divisions  # Divisions of this pattern


class StartTrack(BaseEvent):
    """
    StartTrack - Represents the start of a MIDI track.

    This builtin event is generated when a new MIDI track is encountered.
    This event contains info about the upcoming track.
    """

    name: str = "StartTrack"
    statusmsg = -2

    def __init__(self, chunk_type, length) -> None:

        super().__init__(chunk_type, length)

        self.chunk_type = chunk_type  # Type of track this is
        self.length = length  # Length of this track


class StopPattern(BaseEvent):
    """
    StopPattern - Represents the end of a pattern.

    This event has no special info contained within.
    """

    name: str = "StopPattern"
    statusmsg: int = -3


class UnknownMetaEvent(BaseEvent):
    """
    UnknownMetaEvent - A meta event that we do not know about.
    
    We keep the event data and type for inspection.
    We keep track of these events for debugging purposes,
    instead of silently trashing them.
    
    You probably should not attempt to work with these events
    unless you know what you are looking for!
    """
    
    name: str = "UnknownMetaEvent"
    statusmsg: int = -4

    def __init__(self, status, *args) -> None:
        super().__init__(*args)
        
        self.statusmsg = status  # Status message of the unknown event


class UnknownEvent(BaseEvent):
    """
    UnknownMetaEvent - An event that we do not know about.

    We keep the event data and type for inspection.
    We keep track of these events for debugging purposes,
    instead of silently trashing them.

    You probably should not attempt to work with these events
    unless you know what you are looking for!

    Because MIDI events can take advantage of running status,
    two unknown events may be present!
    The default decoder(ModularDecoder) determines that an unknown event is complete once 
    another status message is encountered.
    This means that if two unknown events utilize running status,
    then we will not encounter a status message,
    and will put the data of both into one UnknownEvent instance.
    """

    name: str = "UnknownEvent"
    statusmsg: int = -5

    def __init__(self, status, *args) -> None:
        super().__init__(*args)

        self.statusmsg = status  # Status message of the unknown event
