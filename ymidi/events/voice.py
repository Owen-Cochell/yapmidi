"""
This file contains all MIDI voice channel events.
These events are primarily used to alter musical aspects of the MIDI instance.
An example of a voice channel event is the NoteOn class,
which toggles a note to it's 'on' state with a given velocity. 
"""

from ymidi.events.base import ChannelMessage


class ChannelVoiceMessage(ChannelMessage):
    """
    ChannelVoiceMessage - Abstract class for voice messages!

    A VoiceMessage is a event that controls a musical aspect of the synth.
    This class is mostly used to identify voice channel events.
    """

    pass


class NoteEvent(ChannelMessage):
    """
    NoteEvent - Abstract class for NoteEvents!

    We define necessary parameters for note events,
    and also act as a way to identify note events.

    Usually, the only classes that use us are 'NoteOn', 'NoteOff', and 'PolyphonicAftertouch'.
    """

    __slots__ = ['pitch', 'velocity']
    length = 2

    def __init__(self, pitch: int, velocity: int) -> None:

        super().__init__()

        self.pitch = pitch  # Pitch of the note, in raw MIDI note format
        self.velocity = velocity  # Velocity of the note, in raw MIDI velocity format


class NoteOn(NoteEvent):
    """
    Represents a NoteOn MIDI event.
    This message is usually sent by pressing a key
    or from other triggering devices.
    When encountered, we should toggle the specified note on.
    """

    statusmsg = b'0x90'
    name = "NoteOn"


class NoteOff(NoteEvent):
    """
    Represents a NoteOff event.
    This message is usually sent when a key is released.
    When encountered, we should toggle the specified note off.
    """

    statusmsg = b'0x80'
    name = "NoteOff"


class PolyphonicAfterTouch(NoteEvent):
    """
    Represents a PolyphonicAfterTouchEvent.
    These events allows for after touch to be applied to individual notes,
    which is a change of velocity after the note is pressed.
    When encountered, the velocity of the note should change dynamically,
    if the receiving component supports it.
    """

    statusmsg = b'0xA0'
    name = "PolyphonicAfterTouch"


class ProgramChange(ChannelVoiceMessage):
    """
    Represents a ProgramChange event.
    These events allow for a program change in a given channel,
    usually a change in instrument.
    The program is represented as an intiger(0-127).
    When encountered, the program of the channel should change.
    """

    statusmsg = b'0xC'
    name = "ProgramChange"
    length = 1

    def __init__(self, program) -> None:
        super().__init__()

        self.program = program  # Program number to switch to


class AfterTouch(ChannelVoiceMessage):
    """
    Represents a change in the aftertouch in a given channel.
    These events allow for the aftertouch of an entire channel to be changed.
    This differs from PolyphonicAfterTouchEvent in the fact this this 
    changes the aftertouch for ALL toggled notes in the channel,
    when the former alters individual notes.
    When encountered, the aftertouch for the entire channel should be changed.
    """

    statusmsg = b'0xD0'
    length = 1
    name = "AfterTouch"

    def __init__(self, velocity) -> None:
        super().__init__()

        self.velocity = velocity


class PitchBendEvent(ChannelVoiceMessage):
    """
    Represents a pitch bent event.
    These events allow for the pitch of voices
    to be bent up or down.
    When encountered, the pitch of the voices should be changed.
    """

    statusmsg = b'0xE0'
    length = 2
    name = "PitchBendEvent"

    def __init__(self, fine, coarse) -> None:

        super().__init__()

        self.fine = fine  # Fine setting for the event
        self.coarse = coarse  # Corse setting for the event


class ControlChange(ChannelVoiceMessage):
    """
    Represents a ControlChange event.
    These events are usually used to modify tone parameters
    with a controller other than a keyboard.
    Each controller has a number(from 0-119), and a value(0-128).
    These events are used to modify these controller numbers.

    Be aware, that we have no idea of what number is mapped to what!
    You should use the higher-level components to help with this.
    """

    __slots__ = ['control', 'value']
    length = 2
    statusmsg = b'0xB0'
    name = 'Control Change'

    def __init__(self, control, value) -> None:

        super().__init__()

        self.control = control  # Control number
        self.value = value  # Value number

