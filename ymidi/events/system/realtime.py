"""
This file contains system real time events.
System real time events are used to synchronize 
clock-based MIDI equipment.
These events serve as uniform timeing information
and do not have channel numbers.

These events are only to be used when in MIDI SYNC mode!
MIDI Sync mode allows devices to be controlled by a master,
which allows the sequenced content to be played back at a constant rate.
"""

from ymidi.events.base import RealTimeMessage
from ymidi.constants import TIMING_CLOCK, START_SEQUENCE, CONTINUE_SEQUENCE, STOP_SEQUENCE, ACTIVE_SENSING, SYSTEM_RESET


class TimingClock(RealTimeMessage):
    """
    The TimingClock event is a System Real Time message
    that is used to synchronize systems.
    They are sent over a MIDI connection at a rate of 24
    per quarter note.

    This allows receivers to synchronize their clocks to this value,
    which allows the song sequence to play at a rate the transmitter expects. 
    """

    statusmsg = TIMING_CLOCK
    name = "TimingClock"


class StartSequence(RealTimeMessage):
    """
    The StartSequence event is a System Real Time message
    that is used to command devices in SYNC mode to start
    at the beginning of the song sequence.

    Upon receipt, we should set our pointer
    to the beginning of the sequence.
    """

    statusmsg = START_SEQUENCE
    name = "StartSequence"


class ContinueSequence(RealTimeMessage):
    """
    The ContinueSequence event is a System Real Time message
    that is used to command devices in SYNC mode to begin
    the sequenced song at it's current position.

    Upon receipt, we should start playing the sequenced song
    at our current position when we receive the next TimingClock event.
    """

    statusmsg = CONTINUE_SEQUENCE
    name = "ContinueSequence"


class StopSequence(RealTimeMessage):
    """
    The StopSequence event is a System Real Time message
    that is used to command devices in SYNC mode to begin
    the sequenced song at it's current position.

    Upon receipt, we should stop playing the sequenced song,
    and log our current song pointer for future use.
    """

    statusmsg = STOP_SEQUENCE
    name = "StopSequence"


class ActiveSensing(RealTimeMessage):
    """
    The ActiveSensing event is a System Real Time message
    that is used to determine if the MIDI connection is still valid.
    Active sensing is optional, and if it is never received then
    the device should operate normally.

    However, once the receiver recognizes an ActiveSensing event,
    then it should assume it will receive a message of some kind
    every 300 ms. If no messages are received,
    then the receiver should assume that the MIDI connection is invalid,
    and should return to a stable state.
    """

    statusmsg = ACTIVE_SENSING
    name = "ActiveSensing"


class SystemReset(RealTimeMessage):
    """
    The SystemReset message is a System Real Time message
    that is used to return devices to their power on state.
    This message should be used sparingly,
    and should NOT be sent automatically upon power up.
    This event should be manually invoked,
    NOT by an automated process
    (i.e automatically sent upon power up).
    """

    statusmsg = SYSTEM_RESET
    name = "SystemReset"


# A tuple of ALL realtime events:

REALTIME_EVENTS = (TimingClock, StartSequence, ContinueSequence, StopSequence, ActiveSensing, SystemReset)
