"""
This file contains IO Modules that can use yap-midi containers.

These can be useful for putting events directly into a container
for manipulation, or extracting these events from a container.
These IO modules also support playback,
meaning that these modules can return events in proper time.

Another purpose of these IO modules is that they can
organize incoming events from another IO module.
This allows for events to come in their proper order.
For example if we are working with the MIDIFile IO module,
then events may not come in order, because concurrent events
in other tracks are not parsed at the same time.
These IO modules will take these events and sort them
(if that functionality is enabled in the container being used),
Thus allowing your MIDI file to be played back properly.
"""

import asyncio
from ymidi.events.base import BaseEvent
from ymidi.io.base import BaseIO, ChainIO
from ymidi.containers import Pattern
from ymidi.protocol import BaseProtocol


class ContainerIO(BaseIO):
    """
    ContainerIO - Uses yap-midi containers to work with events.

    This IO module will input events into a yap-midi container,
    and extract events from the same yap-midi container.
    It's kinda like EchoIO in the sense that you get what you put in,
    but this module has a few extra features that EchoIO lacks.

    One useful application of this IO module is to return 
    events from MIDI files in their proper order.
    The MIDIFile IO module returns events in the order they are encountered.
    This means that any events in other tracks will not be returned
    until the current track is complete.
    Because these tracks are concurrent, you will not
    receive events in the order they were meant to be played.
    This IO module will sort these events(if the container has this functionality enabled),
    and return them in the proper order.

    You can supply a container for this IO module to use.
    Otherwise, it will create a Pattern with default options.
    You can access the object under the 'container' attribute.
    """

    def __init__(self, container=None) -> None:

        super().__init__(BaseProtocol(), None, name='ContainerIO')

        self.container = container if container else Pattern()

    def has_events(self) -> bool:
        """
        Determines if this IO module has any more events to return.

        We do this by checking the index of the container,
        and seeing if it is about to go above the length of the container.

        :return: True if more events, False if not
        :rtype: bool
        """

        return len(self.container) <= self.container.index

    async def get(self) -> BaseEvent:
        """
        Gets an event from the container.

        We call the 'get()' method of the container
        to retrieve the events.
        This means any track handlers attached to the container
        will also be called. 

        :return: Event from the container
        :rtype: BaseEvent
        """

        await asyncio.sleep(0)

        return self.container.get()

    async def put(self, event: BaseEvent):
        """
        Puts an event into the container.

        We append the event to the end of the container,
        which means that the track handlers attached to the container
        will also be called.

        :param event: Event from the container
        :type event: BaseEvent
        """

        await asyncio.sleep(0)

        self.container.submit_event(event)


class PlayContainerIO(ContainerIO):
    """
    PlayContainerIO - Uses yap-midi containers to playback events.

    We are identical to ContainerIO, except that we playback the events
    in a musically valid way.
    This means that this IO module will wait to return the event,
    until it is musically appropriate to do so.
    For example, if an event has a delta time greater than zero,
    then we will wait until the delta time has passed.
    """

    async def get(self) -> BaseEvent:
        """
        Gets an event from the container.

        We call the 'time_get()' method of the container
        to get the events.
        This means any track handlers attached to the container
        will also be called, and this method will
        wait until it is time for the event to play.

        :return: Event from the container
        :rtype: BaseEvent
        """

        return await self.container.time_get()
