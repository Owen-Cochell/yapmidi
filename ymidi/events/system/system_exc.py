"""
This file contains events for System Exclusive messages.
System Exclusive messages are recognized by all receivers, 
and are channel independent.
They are designed to send data of variable length.
Sysexc messages send misc data such as patch parameters,
sampler data, sequencer data, ect.
"""

from ymidi.events.base import BaseSystemExclusiveMessage


class FullSystemExclusiveMessage(BaseSystemExclusiveMessage):
    """
    Base class for SystemExclusive events.
    This class defines some extra functionality 
    that system exclusive events have.
    The biggest addition is the sub-id,
    which is used to identify the system exclusive event.

    This class represents a full System Exclusive message,
    which is a combination of SystemExclusive header
    and data fragments.
    This event(and those that inherit this)
    will be spliced together by an entity,
    and will provide this complete event
    for users to work with.
    """

    __slots__ = ['device']

    statusmsg = b'0xF0'
    name = 'SystemExclusive'
    length = -1
    header = b'0x00'  # Header of the System Exclusive message

    def __init__(self, *args) -> None:
        super().__init__()

        self.data = bytearray(args)



class UniversalSysExc(FullSystemExclusiveMessage):
    """
    Base class for Universal System Exclusive events.

    UniversalSystemExclusive events are primarily used to
    extend the MIDI specification to add extra functionality.
    For example,
    the Sample Dump Standard is done using these messages,
    and it allows samples to be sent to devices via MIDI.

    UniversalSystemExclusive messages are NOT manufacturer defined,
    and are intended to be processed by ALL devices that can handle them.
    """

    header = b'0x00'  # Header of the SystemExclusive event
    subid1 = b'0x00'  # Sub-header 1, used to identify the message
    subid2 = b'0x00'  # Sub-header 2, also used to identify the message
    name = "UniversalSysExc"

    def __init__(self, device, *args) -> None:
        super().__init__(*args)

        self.device = device  # Device ID this message was intended for


class RealTimeSysExc(FullSystemExclusiveMessage):
    """
    The RealTimeSysExc event is a System Exclusive message
    that is used to convey realtime data.
    This data can consist of pretty much anything,
    but it usually refers to data that changes the
    musical prefromance, such as volume,
    bar number, time signature, ect.

    The sub-ids for this class are not specified,
    as they will be defined on the sub-class level.
    """

    header = b'0x7F'
    name = "RealTimeSysExc"


class NonRealTimeSysExc(FullSystemExclusiveMessage):
    """
    The NonRealTimeSysExc event is a System Exclusive message
    that is used to convey non-realtime data.
    Like the class above, this can consist of pretty much anything,
    but it usually refers to data that is NOT relevant to the 
    musical prefromance, such as a sample dump,
    or MIDI Time Code.

    The sub-ids for this class are not specified,
    as they will be defined on the sub-class level.
    """

    header = b'0x7E'
    name = "NonRealTimeSysExc"
