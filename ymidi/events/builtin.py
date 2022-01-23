"""
These events are built into yap-midi.
These events do NOT represent valid MIDI info,
and are instead used to represent things relevant only for yap-midi,
such as start of files and tracks, and end of MIDI files.

ALL builtin events have negative status messages.
"""

from operator import length_hint
from ymidi.events.base import BaseEvent


class StartPattern(BaseEvent):
    """
    StartPattern - Represents the start of a MIDI pattern,
    which is a collection of tracks.
    This builtin event is usually generated when MIDI info is being playedback.
    For example, MIDI file IO modules will generate these events.

    This event contains info about the given pattern,
    which entails the format and divisions.
    """

    name: str = "StartPattern"
    statusmsg: int = -1

    def __init__(self, legnth, format, track_num, divisions) -> None:

        super().__init__(legnth, format, track_num, divisions)

        self.length = legnth  # Length of the pattern header
        self.format = format  # Format of this pattern
        self.track_num = track_num  # Number of tracks in this pattern
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
        self.length = length  # Legnth of this track


class StopPattern(BaseEvent):
    """
    StopPattern - Represents the end of a pattern.

    This event has no special info contained within.
    """

    name: str = "StopPattern"
    statusmsg: int = -3
