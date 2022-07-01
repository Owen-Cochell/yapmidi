"""
This file contains system common events.
System common events are system events that
don't fall into any category.
They are intended for all receivers,
regardless of the channel.
"""

from ymidi.events.base import SystemCommon
from ymidi.constants import SONG_POSITION_POINTER, SONG_SELECT, TUNE_REQUEST, EOX


class SongPositionPointer(SystemCommon):
    """
    Event representing a SongPositionPointer message.

    This event is used to jump to a position in a song,
    which is usually a collection of MIDI events to be played back.
    A 'Song Position' is the number of MIDI beats (1 beat = 6 MIDI clocks)
    that have elapsed from the start of the song.
    This is usually used to jump to a position other than the beginning of the song.

    The Song Position Pointer is used to alter the Song Position,
    so playback can begin at the specified location.
    We accept a LSB and MSB to determine the song pointer.
    """

    statusmsg = SONG_POSITION_POINTER
    name = "SongPositionPointer"
    length = 2

    def __init__(self, lsb, msb) -> None:
        super().__init__(lsb, msb)

        self.lsb = lsb  # Least significant bit
        self.msb = msb  # Most significant bit


class SongSelect(SystemCommon):
    """
    Event representing a SongSelect message.

    This event specifies which song or sequence is to be played upon receipt of 
    a Start message event.
    """

    statusmsg = SONG_SELECT
    length = 1
    name = "SongSelect"

    def __init__(self, song) -> None:
        super().__init__(song)

        self.song = song  # Selected song


class TuneRequest(SystemCommon):
    """
    This class represents a TuneRequest event.

    This event requests that all oscillators be tuned in analog synthesizers.
    Most of the time, this event is ignored by digital synthesizers.
    """

    statusmsg = TUNE_REQUEST
    length = 0
    name = "TuneRequest"


class EOX(SystemCommon):
    """
    This class represents an End of System Exclusive(EOX) flag.

    This event is sent when a system exclusive message is complete.
    """

    statusmsg = EOX
    length = 0
    name = "EOX"


# Tuple of all system common events:

SYSTEM_COMMON_EVENTS = (SongPositionPointer, SongSelect, TuneRequest, EOX)
