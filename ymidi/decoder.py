"""
This file defines decoder objects for yap-midi.

A 'decoder' takes data in a certain format,
and converts said data into a valid MIDI instance.
This is probably not surprising to you,
but you may be interested to hear that decoders
also encode MIDI instances back into the data in the original format!
Neato!

These classes are usually used by IO classes,
but you can use these standalone if you wish.
"""

import asyncio
import struct

from typing import Union, Dict

from ymidi.events.base import BaseEvent
from ymidi.events.voice import VOICE_EVENTS


class BaseDecoder(object):
    """
    BaseDecoder - Class all decoders MUST inherit!

    We define some functionality all decoders must implement.
    We also try to keep decoder implementation ambiguous,
    as decoders can work with pretty much anything!
    We also provide some general helper methods for MIDI decoding.

    We expect decoders to input raw bytes and output yap-midi events,
    and vice versa.
    Users can decode raw bytes by using the decode() method,
    and users can encode yap-midi events by using the encode() method.
    
    The decode() method expects a bytearray 
    """

    def decode(self, bts: bytes) -> BaseEvent:
        """
        Decodes a series of bytes into a valid yap-midi event.

        We only define the functionality for a decoder,
        so we do nothing.

        :param bytes: Bytes to decode
        :type bytes: bytes
        :return: BaseEvent representing the bytes
        :rtype: BaseEvent
        """

        raise NotImplementedError("Must be overridden in child class!")

    def encode(self, event: BaseEvent) -> bytes:
        """
        Encodes a yap-midi event into a series of bytes.

        We only define the functionality for a decoder,
        so we do nothing.

        :param event: Event to encode
        :type event: BaseEvent
        :return: Series of bytes representing the event
        :rtype: bytes
        """

        raise NotImplementedError("Must be overridden in child class!")

    def seq_decode(self, byte: bytes) -> Union[None, BaseEvent]:
        """
        Sequentially decodes the given bytes.

        This method returns None if their is still work to be done,
        and more bytes are required.
        Once the decoding operation is complete,
        then this method will return the event generated from the bytes.

        :param byte: Bytes to work with
        :type byte: bytes
        :return: None if more bytes needed, BaseEvent when decoding operation is complete
        :rtype: Union[None, BaseEvent]
        """

        raise NotImplementedError("Must be overridden in child class!")

    def reset(self):
        """
        Resets the state of this decoder.

        This method is usually used with decoders that are sequential.
        This allows for decoders to be reset to a working state
        if any issues with decoding are encountered.
        """

        pass

    def to_bytes(self, num: int) -> bytes:
        """
        Converts the given intiger into valid bytes.

        We expect only one int to be supplied at a time!

        :param num: Number to convert
        :type num: int
        :return: Encoded bytes
        :rtype: bytes
        """

        # Convert to bytes and return:

        return struct.pack(">B", num)

    def to_int(self, bts: bytes) -> int:
        """
        Converts the given bytes into an intiger.

        We expect only one byte to be supplied at a time!

        :param num: Number to convert
        :type num: bytes
        :return: Intoger representing the bytes
        :rtype: int
        """

        return struct.unpack(">B", bts)[0]

    def is_status(self, num: int) -> bool:
        """
        Determines if this bit is a status byte.

        A status byte will always be between 0-127.
        We return True if the byte is a status byte.

        :param int: Int to check
        :type int: [type]
        :return: True if status byte, False if not
        :rtype: bool
        """

        # Determine status byte and return:

        return 0 <= num <= 127

    def is_data(self, num: int) -> bool:
        """
        Determines if this bit is a data byte.

        A data byte will always be between 128-255.
        We treturn True if the byte is a data byte.

        :param num: Int to check
        :type num: int
        :return: True is data byte, False if not
        :rtype: bool
        """

class ModularDecoder(BaseDecoder):
    """
    ModularDecoder - Decodes raw bytes based upon the events in our collection.

    This class decodes raw bytes based upon the instructions 
    of the events in out collection.
    Here is the standard lifecycle of a decoding operation:

    1.) Get the status message of the data(If not supplied, use running status)
    2.) Retrieve the event instance with the status message
    3.) Get the length of the event
    4.) Instantiate the event with the extra data in the order we received it
    5.) Determine if the event is a channel message, if so attach the channel
    6.) Return the event

    Decoding works in a similar way:

    1.) Encode status message of event, encode channel if necessary
    2.) Get each relevant attributes using __slots__()
    3.) Encode the values
    4.) Return the raw bytes

    This decoder also supports variable length messages,
    but the process for this is very similar.

    We rely on a collection of events that are organized by relevant type.
    This collection orders events into three catagories:

    1.) normal - This event operates normally and requires no extra operations
    2.) channel - This event requires channel information to be worked with
    3.) variable - This event is variable length
    4.) interrupt - This event is allowed to interrupt the data byte flow, and does not affect running status(real time messages)

    This class automatically generates an event collection
    using the default yap-midi events.
    Users can create their own event collection,
    or alter the existing one,
    so the decoder can work with custom user events,
    given the follow the rules outlined here.

    The collection is essentially a dictionary of valid events.
    The key is the status message of the event,
    while the value is the event class to use while generating. 

    This decoder can either be used as an incremental decoder,
    or as an instant decoder.
    The component using this decoder can decide which is the best!
    """

    def __init__(self) -> None:
        super().__init__()

        self.collection: Dict[int, BaseEvent] = {}  # Collection of events
        self.status = None  # statusmesage of the last event processed

    def load_default(self):
        """
        Loads the default events into our collection.

        We simply import the relevant events
        and add it to the collection.
        """

        events = VOICE_EVENTS

        # Iterate over all events in yap-midi:

        for event in events:

            # Add the event to the collection:

            self.collection[event.statusmsg] = event

    def decode(self, bts: bytes) -> BaseEvent:
        """
        Decodes the given bytes into a yap-midi event.

        :param bytes: Bytes to decode
        :type bytes: bytes
        :return: Event representing the bytes
        :rtype: BaseEvent
        """

        # Determine if we are working with a new event:

        if self.is_status(bts[0]):

            # Working with a new event! Set our current status:

            self.status = bts[0]

        # Get the event we are working with:

        event = self.collection[self.status]

        # Determine if the given data is the correct length:

        assert len(bts) - 1 == event.LENGTH