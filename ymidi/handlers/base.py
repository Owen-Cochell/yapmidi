"""
This file contains base components for yap-midi handlers.

An event handler is a piece of code that 
reacts to a certain MIDI event.
A HandlerCollection is a class 
that organizes and works with handlers.

This file ONLY contains the BaseHandler, MetaHandler, and HandlerCollection classes.
Builtin handlers are kept elseware.
"""

import asyncio

from typing import Any, Union, Callable, Awaitable
from collections.abc import Iterable
from collections import defaultdict

from ymidi.misc import ModuleCollection, BaseModule
from ymidi.events.base import BaseEvent


class BaseHandler(BaseModule):
    """
    BaseHandler - Class all event handlers MUST inherit!

    An EventHandler is a component that handles MIDI events in some way.
    This could be anything from printing them,
    altering the state of something, the possibilities are endless!

    Event handlers are usually not used discreetely.
    Instead, they are loaded into the Sequencer,
    which calls them when relevant MIDI events are encountered.

    These modules also support self-reporting event registration,
    meaning that the handler tells the HandlerCollection
    what events this handler is supposed to work with.
    """

    NAME = "BaseHandler"

    def __init__(self, name: str=''):

        super().__init__(name=name)

        self._args: tuple = ()  # Arguments used in callback registration
        self._callback: Callable[[BaseEvent,], Awaitable]  # Callback to be called

    async def handle(self, event: BaseEvent):
        """
        Method called when an event needs to be handled.

        This method is supposed to handle the given event in some way.
        How this is done is left solely up to the developer.

        The event passed is the relevant event 
        that fired off this handler.

        By default, a NotImplementedError is raised when this method is called,
        as it should be overloaded in the child class!

        :param event: Event to be handled
        :type event: BaseEvent
        :raises: NotImplementedError: Should be overloaded in child class!
        """

        raise NotImplementedError("Handle method should be overloaded in child class!")

    async def _run_function(self, event: BaseEvent):
        """
        Runs the external function attached to this handler.

        This method is usually used as the handle method for the handler.
        The external function MUST be a coroutene!

        :param event: Event to handle
        :type event: BaseEvent
        """

        # Run the external function:

        await self._callback(event, *self._args)


class MetaHandler(BaseHandler):
    """
    Metahandler - Class all meta-handlers must inherit!

    Meta handlers are similar to event handlers,
    except that instead of reacting to a MIDI event,
    meta handlers change the MIDI event,
    or the state of yap-midi components.
    For example, 
    a meta-handler might filter out certain MIDI events that are irrelevant.

    Meta-handlers are very useful tools,
    and they can automate certain actions that 
    the user might not want to deal with themselves.

    Meta handlers can be removed or disabled from the HandlerCollection,
    but be aware that doing so could lead to strange experiences
    that might not be encountered with working meta handlers!

    Meta handlers can alter events on their way to the event handlers,
    as well as packets on their way to the output modules.
    It is up to the user to decide which streams the meta handlers effect.

    Meta Handlers also have a built in priority that determines the order of execution.
    This value may get changed by the user loading the handler,
    or by a user who instantiates the meta handler,
    but it is still important to put s good default priority
    that the user may want.
    The lower the number, the higher the priority.
    """

    NAME = "MetaHandler"
    PRIORITY = 20

    def __init__(self, name:str="", priority:int=None) -> None:

        super().__init__(name=name)

        self.priority=self.PRIORITY if priority is None else priority # Priority of this meta handler

    async def handle(self, event: BaseEvent) -> Union[BaseEvent, None]:
        """
        This method is called when an event needs to be handled.

        Here, the meta handler can change and alter the event in any way that is necessary.
        This can range from altering the packet,
        chaning the state of the Sequencer,
        or even dropping the event, and preventing it from being processed.

        This method should return the finalized event.
        If the event should be dropped,
        then None should be returned.
        The Sequencer will NOT further process the packet.

        By default, a NotImplementedError is raised when this method is called,
        as it should be overloaded in the child class!

        :param event: Event to process
        :type event: BaseEvent
        :return: Final event, or None
        :rtype: BaseEvent, None
        :raises: NotImplementedError: Must be overloaded in child class!
        """

        raise NotImplementedError("Must be overloaded in child class!")


class HandlerCollection(ModuleCollection):
    """
    HandlerCollection - Eases the process of working with handlers!

    We offer some easy entry points into handler management,
    mainly indexing and organising handlers so they are tied
    to certain events.
    We also offer the meta handler framework, 
    which allows meta handlers to alter(or drop)
    events before they reach the event handlers.

    We also offer methods to register handlers
    using decorators,
    so users don't have to write an entirely new class for handler management.
    """

    GLOBAL_EVENT = 'global'  # Global event type

    def __init__(self, event_loop=None):

        super().__init__(event_loop=event_loop, module_type=BaseHandler)

        self.meta_map = defaultdict(list) # Tuple of meta events, in order of priority
        self.handler_map = defaultdict(list)  # Dictionary mapping events to handlers
        self.tasks = []  # List of currently running tasks

    def load_handler(self, hand: BaseHandler, event: Union[bytes, Iterable, str]) -> BaseHandler:
        """
        Loads an event handler and registers it to the given event(s).

        The event can be a single status message,
        or it can be an iterable contaning multiple status messages.
        This method will automatically determine the correct way to process the given events.
        If you wish to register the handler to ALL received events,
        then you can use the HandlerCollection.GLOBAL_EVENT parameter.
        This will ensure that your handler is called upon each and every
        event we receive.

        We use ModuleCollection's load_module() method under the hood,
        meaning that this module will be properly loaded into the collection.
        All we do is define some mappings!

        :param hand: Handler to add to the collection
        :type hand: BaseHandler
        :param event: Event(s) to map the handler to
        :type event: bytes, iterable, None
        """

        # Load the event - Make sure it succeeds!

        super().load_module(hand)

        # Add the handler to our mappings:

        self._add_event(self.handler_map, event, hand)

        # Finally, return the handler:

        return hand

    def load_meta(self, meta: MetaHandler, event: Any, priority: int=None) -> MetaHandler:
        """
        Loads the meta handler into our collection.

        Like the load_handler() method,
        we register meta handlers to certain status messages,
        so only the relevant ones are called to process a certain message.
        This can be defined using the 'event' parameter.
        You can provide a single status message as a byte,
        multiple status messages with an iterable,
        or you can register the MetaHandler to ALL events with HandlerCollection.GLOBAL_EVENT.

        Users can also define a priority for the meta handler.
        This will determine the order that the meta handlers 
        are executed in.
        This will change the priority parameter of the meta handler.
        The lower the number, the higher the parameter.
        Leave this value as None to use the default priority value for the handler.

        :param meta: Meta handler to load
        :type meta: MetaHandler
        :param priority: Priority of the handler, optional
        :type priority: int, None, Iterable
        :return: Loaded MetaHandler
        :rtype: MetaHandler
        """

        # Make sure the handler loads correctly:

        self.load_module(meta)

        # Change the priority value if necessary:

        if priority is not None:

            meta.priority = priority

        # Add the MetaHandler to our mappings:

        self._add_event(self.meta_map, event, meta)

        # Finally, return the MetaHandler:

        return meta

    def unload_handler(self, hand: BaseHandler, event: Union[bytes, Iterable]=None) -> BaseHandler:
        """
        Unloads the given handler from our collection.

        Users can optionally provide an event(s) to remove the handler from.
        If provided, we will remove the handler from the given events ONLY!
        If the event is None, then we will remove the handler from ALL events!

        :param hand: Handler to unload
        :type hand: BaseHandler
        :param hand: Event(s) to unload the handler from
        :return: Unloaded handler
        :rtype: BaseHandler
        """

        # Remove the handler:

        self._remove_event(self.handler_map, event, hand)

        # Remove the handler from the collection:

        self.unload_handler(hand)

        # Finally, return the handler:

        return hand

    def unload_meta(self, meta: MetaHandler, event: Any=None) -> MetaHandler:
        """
        unloads the given MetaHandler from the collection.

        Like the remove_handler() method,
        users can optionally provide an event(s) to remove the handler from.
        If provided, we will remove the handler from the given events ONLY!
        If the event is None, then we will remove the handler from ALL events!

        :param meta: MetaHandler to remove
        :type meta: MetaHandler
        :param event: Event(s) to remove the meta handler from
        :type event: bytes, Iterable, None
        :return: MetaHandler we removed
        :rtype: MetaHandler
        """

        # Remove the MetaHandler:

        self._remove_event(self.meta_map, event, meta)

        # Unload the handler from the collection:

        self.unload_handler(meta)

        # Finally, return the MetaHandler:

        return meta

    def callback(self, func: Callable[[BaseEvent,], Awaitable], event: Union[bytes, Iterable], name:str='', args:list=None):
        """
        Adds the given function to the HandlerCollection as a callback.
        The function provided MUST be an asyncio coroutene!

        This method is intended to be used as a decorator:

        .. code-block:: python

            from ymidi.handlers.base import HandlerCollection
            from ymidi.const import Events TODO: Fix this line!

            # Create the HandlerCollection:

            hands = HandlerCollection()

            # Make some function:

            @hands.callback(Events.NOTE_ON)
            async def some_func(hand, event):
                # Do something with the event:

                pass

        This will register the function to the given events.
        We do this by creating a BaseHandler,
        and setting it's handle() method to the provided function.
        We then configure this handler,
        and then register it like any other handler.
        This allows developers to register functionality
        without having to write handler classes.

        The function should take at least two parameters,
        the first which will be the instance of the BaseHandler
        the function is a member of.
        The function can use this parameter to access the HandlerCollection,
        and do some other cool things.

        The second parameter will be the relevant event passed to the function.
        This is an event handler,
        so the function should react in some way to the event.

        Users can specify the args to pass to the function at runtime using the 'args' parameter.

        :param func: Function to register
        :type func: function
        :param events: Events to register the function to, defaults to None
        :type events: Union[bytes, Iterable], optional
        :param name: Name of the handler, defaults to ''
        :type name: str, optional
        :param args: Arguments to pass to the function at runtime
        :type args: list
        """

        # Let's create a dummy BaseHandler:

        temp = BaseHandler(name=name)

        # Set the args:

        if args is not None:

            temp._args = tuple(args)

        # Set the function:

        temp._callback = func

        # Set the callback runner:

        temp.handle = temp._run_function

        # Register the handler with the given events:

        self.load_handler(temp, event)

    def sync_submit(self, event: BaseEvent):
        """
        Synchronously sends the event thorugh the handlers.

        This code is intended to be ran by synchronous code
        that needs to handle a given event.

        We simply call the underlying submit() method.

        :param event: Event to handle
        :type event: BaseEvent
        """

        self.event_loop.run_until_complete(self.submit(event))

    async def submit(self, event: BaseEvent):
        """
        Submits the given event to the HandlerCollection.

        First, the relevant meta handlers are ran in order.
        This prepares the event for handling,
        and allows the meta handlers to do whatever they need to do.

        Next, the relevant handlers are located for this event,
        usually the catch-all handlers and the ones registered to the status message.
        Each handler is sent to their own task,
        where they can react to the event as they see fit.

        After these tasks are complete,
        this function will exit.

        :param event: Event to process
        :type event: BaseEvent
        """

        temp = await self.meta_handle(event)

        if temp is None:

            # Invalid event! Let's do nothing:

            return

        event = temp

        # Run the event though the event handlers:

        await self.event_handle(event)

    async def meta_handle(self, event: BaseEvent) -> Union[BaseEvent, None]:
        """
        Sends the given event thorugh this collection's meta handlers.

        This method will send in event through all meta handlers
        in order of priority and return the end result.

        If a packet is dropped,
        then we will simply return None.

        We only run the relevant meta handlers for this event.

        :param event: Event to be handled
        :type event: BaseEvent
        :return: Final event, or None
        :rtype: BaseEvent, None
        """

        # Get a list of MetaHandlers:

        meta = self.meta_map[None] + self.meta_map[event.statusmsg]

        for hand in meta:

            # Await the MetaHandler:

            event = await hand.handle(event)

            # Check if the event is valid:

            if event is None:

                # Invalid event! Return without processing

                return None

        return event

    async def event_handle(self, event: BaseEvent):
        """
        Sends the event through all event handlers.

        This method will NOT send the event through the meta handlers,
        so be sure to call the meta_handle() method to do so(good),
        or the submit() method which does this operation for you(best).

        We run each event handler in an asyncio task for 'concurency'.
        Event handlers should not alter the state of this collection,
        so it is safe to run them at the same time.

        We only run the relevant event handlers attached to this event.

        :param event: Event to handle
        :type event: BaseEvent
        """

        # Now that the event is processed, let's get the relevant EventHandlers:

        hands = self.handler_map[None] + self.meta_map[event.statusmsg]

        # Process the events!

        final = await asyncio.gather(*hands)

    def _get_priority(self, val: MetaHandler) -> int:
        """
        Gets the priority of the meta handler.

        Mostly used for meta handler sorting.

        :param val: Meta handler to get priority of
        :type val: MetaHandler
        :return: Priority of the MetaHandler
        :rtype: int
        """

        # Get and return the priority:

        return val.priority

    def _add_event(self, struct: dict, event: Any, hand: BaseHandler):
        """
        Processes the given event depending on type.

        :param struct: Structure to change
        :type struct: dict 
        :param event: Event(s) to change
        :type event: str, bytes, Iterable
        :param hand: Handler to change
        :type hand: BaseHandler
        """

        if isinstance(event, Iterable):

            # Register the handler to ALL given events:

            for msg in event:

                # Register the handler:

                struct[msg].append(hand)

        elif event == HandlerCollection.GLOBAL_EVENT:

            # Register the event to ALL events:

            struct[HandlerCollection.GLOBAL_EVENT].append(hand)

        else:

            # Some other event type, let's register it anyway:

            struct[event].append(hand)

    def _remove_event(self, struct: dict, event: Any, hand: BaseHandler, remove: bool=False):
        """
        Removes the given handler from the structure,
        operating under the instructions of the event type.

        :param struct: Structure to change
        :type struct: dict 
        :param event: Event(s) to change
        :type event: str, bytes, Iterable
        :param hand: Handler to change
        :type hand: BaseHandler
        :param remove: Value determining if we should remove the handler instead of add it
        :type remove: bool 
        """

        if isinstance(event, Iterable):

            # Register the handler to ALL given events:

            for msg in event:

                # Remove the handler:

                struct[msg].remove(hand)

        elif event is None:

            # Remove the handler from ALL events:

            for val in self.handler_map.values():

                for temp in val:

                    if hand == temp:

                        # Remove the handler:

                        val.remove(hand)

        elif event == HandlerCollection.GLOBAL_EVENT:

            # Remove the handler from global events:

            struct[HandlerCollection.GLOBAL_EVENT].remove(hand)

        else:

            # Remove the handler from the given event:

            struct[event].remove(hand)
