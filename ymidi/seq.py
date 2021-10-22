"""
High-level yap-midi components.

This file contains the Sequencer class,
which is the recommended way of using yap-midi,
as well as handlers that can be used in this class.
"""

import asyncio
from ymidi.events.base import BaseEvent

from ymidi.handlers.base import HandlerCollection
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

                                  +--> Meta Handlers --> Event Handlers
    Input IO modules -> Sequencer +
                                  +--> Meta Handlers --> Output IO Modules

    As you can see,
    we retrieve an event from the input IO modules,
    and then concurrently send it through the relevant meta handlers for each path.
    The meta handlers from the event handlers and the output IO modules are diffrent,
    which allows events to be altered depending upon where it is going.

    We synchronize the asyncio event loop across all components.
    """

    def __init__(self) -> None:

        super().__init__(event_loop=asyncio.get_event_loop())

        self.input = IOCollection(event_loop=self.event_loop)  # IO Collection for input
        self.output = IOCollection(event_loop=self.event_loop)  # IO Collection for output
        self.output_meta = HandlerCollection()  # Output meta handlers

        # Setting the default handler to output to the output IO modules:

        self.output_meta.callback(self._output_event, HandlerCollection.GLOBAL_EVENT, name="IOModule Output")

        # Submit the run task:

        self.event_loop.create_task(self.run())

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

            # Send the event through our event handlers and the output modules:

            final = await asyncio.gather(self.submit(event), self.output_meta.submit(event))

    async def _process_output(self, event: BaseEvent):
        """
        Sends the given event through the output meta handlers,
        as submits it to the output IOCollection.

        :param event: Event to process
        :type event: BaseEvent
        """

        # Process the event:

        await self.output_meta.submit(event)

    async def _output_event(self, hand: HandlerCollection, event: BaseEvent):
        """
        Outputs the given event to the output IO modules.

        :param hand: Instance of us
        :type hand: HandlerCollection
        :param event: Event to output
        :type event: BaseEvent
        """

        # Output the event:

        await self.output.put(event)
