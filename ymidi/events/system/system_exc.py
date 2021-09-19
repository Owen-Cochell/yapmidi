"""
This file contains events for System Exclusive messages.
System Exclusive messages are recognized by all receivers, 
and are channel independent.
They are designed to send data of variable length.
Sysexc messages send msic data such as patch parameters,
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

    def __init__(self, data) -> None:
        super().__init__()

        self.data = bytearray(data)


class RealTimeSysExc(FullSystemExclusiveMessage):
    """
    The RealTimeSysexc event is a System Exclusive message
    that is used to convey realtime data.
    This data can consist of pretty much anything.

    The sub-ids for this class are not specified,
    as they will be defined on the sub-class level.
    """

    header = b'0x7F'
    name = "RealTimeSysExc"
    subid1 = b'0x00'
    subid2 = b'0x00'

    def __init__(self, *data) -> None:
        super().__init__(data)
