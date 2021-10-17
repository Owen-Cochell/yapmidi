"""
High-level yap-midi components.

This file contains the Sequencer class,
which is the recommended way of using yap-midi,
as well as handlers that can be used in this class.
"""

import asyncio

from ymidi.handlers.base import BaseHandler, HandlerCollection
from ymidi.io.base import IOCollection


class YMSequencer(HandlerCollection):
    """
    YMSequencer - High-level yap-midi class!

    The sequencer is the top-level class for yap-midi development.
    It coordinates and synchronizes input IO modules,
    event handlers, and output IO modules.

    This class is intended to be used by the end user,
    as it seeks to simplify and automate the components 
    used to retrieve, send, and handle MIDI events.

    One of the many features of this class is event handlers.
    Whenever an event is captured,
    any relevant event handlers attached to the event will be called.
    This allows users to use the YMSequencer as a framework
    for reacting to MIDI messages.

    YMSequencer also offers a meta-handler framework.
    A meta-handler is a event handler that changes the state
    of the packets,
    or other yap-midi components,
    before they reach the event handlers.
    This allows for MIDI events to be filtered,
    normalized, and otherwise altered to make handling them a breeze. 

    Finally, YMSequencer eases the process of using IO modules,
    and allows for MIDI events to be transferred to another location 
    once the meta handlers have finished processing the events.

    The event lifecycle looks something like this:

                                      +--> Event Handlers
    Input IO modules -> Meta Handlers +
                                      +--> Output IO modules

    As you can see,
    the event lifecycle is linear until the meta handlers
    finish processing the event.
    From there, the finalized event is passed along
    to the event handlers for processing,
    and the output IO modules for sending them elseware.

    We synchronize the asyncio event loop across all components.
    """

    def __init__(self) -> None:

        super().__init__(event_loop=asyncio.get_event_loop())

        self.input = IOCollection(event_loop=self.event_loop)  # IO Collection for input
        self.output = IOCollection(event_loop=self.event_loop)  # IO Collection for output

    def get_input(self) -> IOCollection:
        """
        Gets and returns the input IOCollection.

        Users can alter this class in any way they see fit,
        usually adding/removing modules.

        :return: Input IOCollection
        :rtype: IOCollection
        """

        return self.input

    def get_output(self) -> IOCollection:
        """
        Gets and returns the output IOCollection.

        users can alter this class in any way they see fit,
        usually adding/removing modules.

        :return: Output IOCollection
        :rtype: IOCollection
        """

        return self.output

    async def run(self):
        """
        Runs the sequencer and all components.

        In this method we get events from the input IOCollection,
        route them though the meta handlers,
        and 'concurrently' send the output event to the event handlers and the output IOCollection.

        This is where the magic happens!
        All components are utilized here,
        and this method of the Sequencer
        is how MIDI processing gets done.
        """

        # Loop until we stop:

        while self.running:

            # Get an event from the Input IO Modules:

            event = await self.input.get()

            # Send the event though the meta handlers:

            event = await self.meta_handle(event)

            if event is None:

                # Dropping the event, let's exit:

                return

            # Send the event to the output modules and event handlers:

            final = asyncio.gather(self.event_handle(event), self.output.put(event))
