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
from ctypes.wintypes import MSG
from lib2to3.pytree import Base
import struct

from typing import Any, Union, Dict, Tuple

from ymidi.events.base import BaseEvent, BaseMetaMesage
from ymidi.events.voice import VOICE_EVENTS
from ymidi.events.system.realtime import REALTIME_EVENTS
from ymidi.events.system.common import SYSTEM_COMMON_EVENTS
from ymidi.events.system.system_exc import SYSTEM_EXCLUSIVE_EVENTS
from ymidi.events.meta import META_EVENTS
from ymidi.constants import META


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

        A status byte will always be between 128-255.
        We return True if the byte is a status byte.

        :param int: Int to check
        :type int: [type]
        :return: True if status byte, False if not
        :rtype: bool
        """

        # Determine status byte and return:

        return 128 <= num <= 255

    def is_data(self, num: int) -> bool:
        """
        Determines if this bit is a data byte.

        A data byte will always be between 0-127.
        We return True if the byte is a data byte.

        :param num: Int to check
        :type num: int
        :return: True is data byte, False if not
        :rtype: bool
        """

        return 0 <= num <= 127


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

    Encoding works in a similar way:

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
    
    TODO: Implement checks to ensure interrupts are valid?
    """

    def __init__(self) -> None:
        super().__init__()

        self.collection: Dict[int, Any] = {}  # Collection of events
        self.decode_status = []  # statusmessage of the last event decoded
        self.encode_status = []  # Statusmessage of the last event encoded

        # --== Sequential Decoding State: ==--

        self.data = []  # Data we are currently working with
        self.event = []  # Event instances to work with

    def load_default(self):
        """
        Loads the default events into our collection.

        We simply import the relevant events
        and add it to the collection.
        """

        events = VOICE_EVENTS + REALTIME_EVENTS + SYSTEM_COMMON_EVENTS + SYSTEM_EXCLUSIVE_EVENTS

        # Iterate over all events in yap-midi:

        for event in events:

            # Add the event to the collection:

            self.load_event(event)

    def load_event(self, event: BaseEvent):
        """
        Loads the given event to the collection.
        
        We first ensure that this event is valid
        (inherits BaseEvent),
        and the we register it for use.

        :param event: Event to register
        :type event: BaseEvent
        """

        if not isinstance(event, BaseEvent):

            # Not a valid event, raise an exception!

            raise ValueError("Event does not inherit BaseEvent!")

        if event.has_channel:
            
            # Encode channel info into the event:
            
            for item in range(0,16):
                
                self.collection[event.statusmsg & 0xF0 | item] = event

        # Add the event:

        else:

            self.collection[event.statusmsg] = event

    def get_legnth(self, status: int) -> int:
        """
        Gets the length of the event using the given status message.
        
        We use our collection of events to retrieve the legnth.

        :param status: Status message of the event
        :type status: int
        :return: Length of event in bytes
        :rtype: int 
        """
        
        return self.collection[status].length

    def decode(self, bts: bytes) -> BaseEvent:
        """
        Decodes the given bytes into a yap-midi event.

        If the status byte is not provided,
        then we will use running status to determine 
        the event type.
        
        This method does NOT support MIDI event interruption.
        Because of this, it is recommended to use this method
        on byte sources that are guaranteed to be structured
        and organized correctly.
        This also means this method will be faster than sequential decoding!
        TODO: Confirm this and backup with some numbers

        :param bytes: Bytes to decode
        :type bytes: bytes
        :return: Event representing the bytes
        :rtype: BaseEvent
        """

        # Determine if we are working with a new event:

        if self.is_status(int.from_bytes(bts[0], 'big')):

            # Working with a new event! Set our current status:

            self.decode_status[0] = bts[0]

        # Get the event we are working with:

        event = self.collection[self.decode_status[0]]

        # Decode the values:

        val = []

        for item in bts[0:]:

            val.append(int(item))

        # Are we a variable length event?
        
        if event.length == -1:

            # Ensure the last value is the end event:
            
            assert val[-1] == event.end.status
            
            # Remove the last data value:
            
            val.pop(-1)

        # Create the event:

        final = event(*val)

        # Determine if event is channel message:

        if final.has_channel:

            # Attach channel data:

            final.channel = self.decode_status[0] & 0x0F

        # Return the final event:

        return final

    def seq_decode(self, bts: bytes) -> Union[None, BaseEvent]:
        """
        Sequentially decodes the given bytes.

        This method processes individual bytes in a sequence,
        which is great if you don't know the length of your events,
        or you can't structure your bytes.

        This method returns None when more bytes are required to decode,
        and returns the final event when the decoding operation is completed.

        Event interruption is supported in this method!
        If you are unsure if out of place MIDI events will interrupt the stream,
        then you should use this method to sort out the chaos.

        :param byte: Byte to decode
        :type byte: bytes
        :return: None if more bytes are required, event if operation is completed
        :rtype: Union[None, BaseEvent]
        """

        num = int.from_bytes(bts, 'big')
        done = False

        # Determine if we are working with a status byte:

        if self.is_status(num):

            # Get the event:

            event = self.collection[num]

            # Check if the event is end of variable length sequence:

            if self.event and self.event[0].length == -1 and self.event[0].end.statusmsg == num:

                # We came to the end of the sequence, exit time:

                done = True

            # Check if the event is ready to be returned now:

            elif event.length == 0:

                # Return the event, save us some time:

                return event()

            else:

                # Configure some data:

                self.decode_status.insert(0, num)
                self.data.insert(0, [])
                self.event.insert(0, event)

                return None

        else:

            # Add the byte to the data buffer:

            self.data[0].append(bts)

        # Check if the data is ready to return:

        if done or (len(self.data[0]) == self.event[0].length):

            # Create the event:

            event = self.event[0](*self.data[0])

            # Clear the decoding state:

            self.data[0].clear()

            # Check if we have to add a channel:

            if event.has_channel:
                
                # Add the event:
                
                event.channel = self.decode_status[0] & 0x0F

            # Check if we are a nested event:

            if len(self.decode_status) > 1:

                # We have other events to process:

                self.decode_status.pop(0)
                self.data.pop(0)
                self.event.pop(0)

            # Return the event:

            return event

        # Not done, return None

        return None

    def encode(self, event: BaseEvent) -> bytes:
        """
        Encodes the given event into bytes.

        :param event: Event to encode
        :type event: BaseEvent
        :return: Encoded bytes
        :rtype: bytes
        """

        # Get the status message of the event:
        
        status = event.statusmsg
        
        # Determine if we are working with channels:
        
        if event.has_channel:
            
            # Encode the channel number in the status message:

             status = status & 0xF0 | event.channel
        
        # Return the final data:
        
        return bytes((status,) + event.data)


class MetaDecoder(BaseDecoder):
    """
    MetaDecoder - Decodes Meta Events present in MIDI files.
    
    Because Meta events are specific to MIDI files,
    and that decoding them is somewhat non-standard,
    decoding operations for them are placed into a separate class
    that is only used when necessary.
    
    A meta event has a status message of 0xFF,
    and has a 'type', 'length', and 'bytes' fields.
    We use these fields to determine the type of event.
    
    From here, it is quite simple as we are given the legnth of the event,
    so we just read a specific amount of bytes.
    
    This encoder is modular, similar to the ModularDecoder,
    which allows custom meta events to be registered and loaded for proper decoding.
    We inherit the BaseDecoder, and use it to decode any non-meta events.
    """
    
    def __init__(self) -> None:
        super().__init__()
        
        self.meta_collection: Dict[int, Any] = {}  # Collection of meta events
    
    def load_default(self):
        """
        Loads the default meta-handlers.
        
        We also load the default events as specified in the ModularDecoder.
        """
        
        for event in META_EVENTS:
            
            # Add each meta event:
            
            self.load_event(event)
        
    def load_event(self, event: BaseEvent):
        """
        Loads the given event.

        If we are working with a meta-event,
        then we load it into the meta collection.
        If this is not a meta event,
        then we send it along to the ModularDecoder for loading.

        :param event: Event to be loaded
        :type event: BaseEvent
        """

        if not isinstance(event, BaseEvent):

            # Not a valid event, raise an exception!

            raise ValueError("Event does not inherit BaseEvent!")

        # Check if the event is a meta event:
        
        if event.statusmsg == MSG:
            
            # Valid meta event, load it:
            
            self.meta_collection[event.type] = event
            
        else:
            
            # Not a meta event, pass it along:
            
            super(BaseDecoder).load_event(event)
    
    def decode(self, bts: bytes) -> BaseMetaMesage:
        """
        Decodes the given bytes into a Meta Event.
        
        We expect ALL meta event bytes to be present,
        including the status message, type, and length felids.

        :param bts: Bytes to decode
        :type bts: bytes
        :return: Valid MetaEvent
        :rtype: BaseEvent
        """

        # Check if the first byte is a valid status message

        if bts[0] is not META:
            
            # Not a meta event, pass it along:
            
            return super(ModularDecoder).decode(bts)
        
        # Get the event instance to work with:
        
        event = self.collection[bts[1]]
        
        # Check the legnth of the event:
        
        pass
        