"""
This file contains classes that work with MIDI Time Code(MTC) events.
MTC events are used to synchronize the time between two devices.
These events are rarely used in the context of musical prefromance,
and many users will simply ignore them.
"""

from ymidi.events.base import SystemCommon


class MIDITimeCode(SystemCommon):
    """
    Base class for MIDI Time Code events.

    These events are primarily used for device time synchronization.
    The events consist of Quarter Frames, Full Frames, and SMPTE events
    for encoding SMPTE user bits.
    These events are usually used in low-level applications,
    and are generally irrelevant to the user. 
    """

    pass


class MTCQuarterFrame(SystemCommon):
    """
    Represents a MTCQuarterFrame event.

    This event is primarily used in device synchronization.
    Each MTC Quarter Frame contains a type and value parameter.
    This event only contains the value for ONE parameter,
    meaning the receiver needs 8 MTCQuarterFrame events
    to compile a complete time code message.

    Here is a list of types:

    * 0 - Frame count LS nibble
    * 1 - Frame count MS nibble
    * 2 - Seconds count LS nibble
    * 3 - Seconds count MS nibble
    * 4 - Minutes count LS nibble
    * 5 - Minutes count MS nibble
    * 6 - Hours count LS nibble 
    * 7 - Hours count LS nibble
    """

    __slots__ = ['type', 'value']
    statusmsg = 0xF1

    def __init__(self, type: int, value: int) -> None:
        super().__init__()

        self.type = type
        self.value = value
