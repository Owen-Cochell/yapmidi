"""
This file contains various builtin meta handlers.

These meta handler can be very useful for
filtering/altering events,
as well as changing the state of yap-midi
when certain events are received.

TODO:
Controller mapper
NoteOn optimizations(Opposite of OntoOff)
General MIDI setup?
Sys exc. adder?
"""

import asyncio

from typing import Any, Union
from ymidi import events

from ymidi.handlers.base import MetaHandler
from ymidi.events.base import BaseEvent, ChannelMessage
from ymidi.constants import CHANNELS, NOTE_ON
from ymidi.events.voice import NoteOff, NoteOn


class EventFilter(MetaHandler):
    """
    EventFilter - Filters MIDI events

    This meta handler allows events to be filtered.
    We will ALWAYS return None upon being handled,
    which will drop the events we are registered to.

    Use this class with caution!
    Be sure to not accidentally register this meta handler to an important event,
    unless this is your intention! 
    """

    NAME = "EventFilter"
    PRIORITY = 1
    
    async def handle(self, event: BaseEvent) -> None:
        """
        As stated above, we simply return None to drop the event

        :param event: Event to filter
        :type event: BaseEvent
        :return: None
        :rtype: None
        """

        # Return None:

        return None


class AdvancedEventFilter(MetaHandler):
    """
    AdvancedEventFilter - Filters events with a twist!

    We are very similar to EventFilter.
    However, we have the added functionality of calling 
    external code to check if the event is valid.

    We use a checker function to determine if the event is valid.
    The checker function should return True for a valid event,
    and False for an invalid event.
    We will drop invalid events,
    and let valid events pass through unaltered.
    You can pass your checker function to the 'checker' parameter
    during instantiation.
    Any extra arguments will be passed along to the checker function.
    Your checker function should take at least one argument,
    which will be the event to check.
    THIS CHECKER FUNCTION MUST BE AN ASYNCIO COROUTENE!

    Because function calls can be somewhat expensive performance wise,
    we are separate from EventFilter,
    as some people want to always drop events regardless of their content or external factors.
    be sure that your checker function is fast enough for high speed processing!

    The same logic applies from EventFilter,
    be careful which events your register this handler under!
    We MIGHT drop events depending on the checker function,
    so make sure this won't drop important events!
    """

    NAME = "AdvancedEventFilter"
    PRIORITY = 1

    def __init__(self, checker: Any, *args, **kwargs) -> None:
        super().__init__()

        self.checker = checker  # Checker function
        self.args = args  # Args to pass to the checker function
        self.kwargs = kwargs  # Keyword args to pass to the checker function

    async def handle(self, event: BaseEvent) -> Union[BaseEvent, None]:
        """
        Checks the given event against our checker function.

        :param event: Event to check
        :type event: BaseEvent
        :return: Returns event if valid, None if not
        :rtype: Union[BaseEvent, None]
        """

        # Run our checker function:

        result = await self.checker(event, self.args, self.kwargs)

        # Check our result:

        if result:

            # Passed the check! Return the event:

            return event

        # Failed the check, return None:

        return None


class OnToOff(MetaHandler):
    """
    Maps NoteOn events with velocity of 0 to NoteOff event handlers.

    According to the MIDI specs, notes can be toggled off by
    sending a NoteOff event, or by sending a NoteOn event with a velocity of zero.
    Most MIDI devices will opt in for the second option,
    as it avoids sending a status byte, which will allow for some time to be saved.

    Because of this, many developers will have to deal with events
    being passed to the NoteOn handlers that are meant to stop notes instead of stop them.
    This MetaHandler will convert NoteOn events with a velocity of 0
    into NoteOff events with a velocity of 64, which is the default velocity value.
    Users can optionally provide a custom velocity value to set as default.

    We should really only be attached to the event handler,
    and NOT the meta handlers for output modules!
    Converting the NoteOn objects into NoteOff objects 
    will change the running status, thus causing 
    the MIDI connection to loose some optimizations.
    Because of this, it is recommended for outgoing events
    to not get converted, as it will save some bandwith.
    TODO: Explain this concept better
    """

    KEYS = (NOTE_ON)

    def __init__(self, velocity=64, name='') -> None:
        super().__init__(name=name)

        self.velocity = velocity  # Value to set the NoteOff value as

    async def handle(self, event: NoteOn) -> Union[BaseEvent, None]:
        """
        Checks if we should convert the event into a NoteOff event.

        :param event: Event to process
        :type event: BaseEvent
        :return: Final event to return
        :rtype: Union[BaseEvent, None]
        """

        # Check if the event has a zero velocity:

        if event.velocity == 0:

            # Convert the event:

            return NoteOff(event.pitch, self.velocity)

        # Otherwise, return the event given:

        return event


class ChannelMap(MetaHandler):
    """
    Maps ChannelMessages to new events.

    By default,
    yap-midi maps channel messages to the same key,
    because the status message of the event is unchanging.

    For example,
    the status message for NoteOn events changes based upon it's channel.
    The NoteOn status message for channel five(0x85)
    is diffrent then the note on message for channel 15(0x8f).
    Because the yap-midi events have unchanging status messages,
    every NoteOn message will get sent to the same handler(0x80).
    The handler at that key may have to determine the channel
    the event is on before it works with it.
    This may be desirable, but some developers may want events to be sorted by channel.

    This meta handler will do just that!
    We combine the status message of the event and the channel number
    into one value, thus allowing for handler to be assigned to events on certain channels.

    For example, when using this meta handler,
    a developer can configure a handler work with AfterTouch events
    that are ONLY on channel 3.
    Users can expand this logic to the other events.

    We have no understanding of the events that we work with!
    We combine the hard coded status message and the channel
    number(in hex format) and use that value as a key.
    We then setup a temporary event map and set the event handlers
    under said key to be ran upon handling the event we worked with.
    Keep in mind, that due to the nature of temporary event maps,
    the event handler(if any) mapped to the hardcoded status message
    of the event will also be called.
    This can be useful if you want a handler to work with ALL events,
    regardless of the channel.

    WE SHOULD ONLY WORK WITH CHANNEL MESSAGES!

    If we work with global messages that do not belong to a channel,
    then this meta handler will defiantly fail,
    which will likely cause other yap-midi components to fail as well.
    By default, we tell the HandlerCollection to load us to all channel messages,
    but the user can load us to non-channel events.
    Don't be that user!
    """

    KEYS = CHANNELS

    async def handle(self, event: ChannelMessage) -> Union[BaseEvent, None]:
        """
        Does the dirty work of event handling.

        As stated in this classe's docstring,
        we combine the channel and status message of the event.

        :param event: Event to work with
        :type event: BaseEvent
        :return: The same event we were given
        :rtype: Union[BaseEvent, None]
        """

        # Get the true key:
        
        key = event.statusmsg & 0xF0 | event.channel

        # Setup a temporary mapping:

        self.collection.map_temp(event, key)
