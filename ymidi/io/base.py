"""
Base classes for IO components.

As stated in the __init__ file for this submodule,
IO classes specialize in inputting/outputting MIDI
data to certain locations.
This is done by using a variety of protocol/decoder objects.

This file contains some base classes for IO modules,
as well as some good debug classes.
If you are a user you probably don't want to work with most of these!
"""

import asyncio
from typing import Tuple

from ymidi.protocol import BaseProtocol
from ymidi.decoder import BaseDecoder
from ymidi.events.base import BaseEvent
from ymidi.misc import BaseModule, ModuleCollection


class BaseIO(BaseModule):
    """
    BaseIO - base class all IO modules MUST inherit!

    We define some features IO modules must inherit.
    This class does not do much on its own,
    but it acts as an important building block!
    We define the methods that an IO module NEEDS to implement,
    such as get() and put().
    We derive our meta functionally from BaseModule.

    An IO module is a class that gets info from somewhere.
    """

    NAME = "BaseIO"

    def __init__(self, proto: BaseProtocol, decoder: BaseDecoder, name: str="") -> None:

        super().__init__(name=name)

        self.proto = proto  # Protocol object in use
        self.decoder = decoder  # Decoder in use

    async def get(self) -> BaseEvent:
        """
        Get and return a valid yap-midi event!

        This function ideally should get raw data from a protocol object,
        decode it using a decoder, and post-process the data as necessary.
        Once these operations are complete, then the event should be returned.
        """

        raise NotImplementedError("Must be overloaded in child class!")

    async def put(self, event: BaseEvent):
        """
        Put the event into the backend we support!

        This function ideally should convert the event back into raw data using the decoder,
        and then pass this data along to the protocol object,
        which will then in turn send the data to wherever it needs to go.
        """

        raise NotImplementedError("Must be overloaded in child class!")


class NullIO(BaseIO):
    """
    NullIO - Does nothing!

    As per the name, we input nothing and output nothing.
    This is the default IO module,
    as it ensures nothing unexpected happens.
    """

    NAME = "NullIO"

    async def get(self) -> None:
        """
        Return 'None'

        :return: None
        :rtype: None
        """

        return None

    async def put(self, event: BaseEvent):
        """
        Do nothing with the event

        :param event: Event to be processed
        :type event: BaseEvent
        """

        pass


class IOCollection(ModuleCollection):
    """
    IOCollection - Manages IO modules!

    This class manages, organises, and works with IO modules.
    We allow for the registration of multiple IO modules,
    and await them all asynchronously.
    This allows for MIDI data to come from many sources at once!

    We also manage the state of these modules,
    enabling and disabling them automatically so the user does not have to.
    The developer can rest easy knowing the proper methods
    will be called at the proper times.

    TODO: Enter the name of main class
    We integrate nicely with the [NAME OF MAIN CLASS HERE],
    but we can be used discreetly.
    Methods are provided to run asyncio tasks in another thread,
    allowing synchronous code to continue.
    This class will also provide methods to send events to all modules,
    allowing all modules to output events using just one call.

    We operate off a queue based model,
    meaning that events are added to a queue as the modules 
    encounter events.
    This allows for events to accumulate until they are needed,
    and for code to block until an event is encountered.
    This queue can be manipulated with our methods.
    Advanced compontens will bypass these methods and access the queue directly.

    TODO: Check out this list!
    - Implement better queue entry points
    - Some runner system for multi-threaded code?
    - TESTING!
    """

    def __init__(self, event_loop=None) -> None:
        
        super().__init__(event_loop, BaseIO)

        self.queue = asyncio.queues.Queue()  # Output queue that holds events

        self.tasks = ()  # Tuple mapping modules to tasks

        self.modules: Tuple[BaseIO,...] = ()

    async def get(self) -> BaseEvent:
        """
        Gets an event from our queue.

        :return: yap-midi event
        :rtype: BaseEvent
        """

        return await self.queue.get()

    async def put(self, event: BaseEvent):
        """
        Sends the given event to each module for output.

        :param event: Event to put in modules
        :type event: BaseEvent
        """

        # Iterate over all modules:

        for mod in self.modules:

            # Put the event into each module:

            await mod.put(event)

    def sync_get(self) -> BaseEvent:
        """
        Gets an event from the queue synchronously.

        This allows for Non-asynchronous code
        to interact with the IO Queue.

        We utilise the event loop to run the async code.

        :return: BaseEvent object retrieved from the queue.
        :rtype: BaseEvent
        """

        # Put the get method in the event loop:

        return self.event_loop.run_until_complete(self.get())

    def sync_put(self, event: BaseEvent):
        """
        Puts the given event into the event queue.

        This allows for Non-asynchronous code to interact with the IO queue.

        Like sync_get(), we utilise the event loop to run the async code.

        :param event: BaseEvent object to add to the queue
        :type event: BaseEvent
        """

        # Run put() method in event loop:

        return self.event_loop.run_until_complete(self.put(event))

    def load_module(self, module: BaseIO) -> BaseIO:
        """
        We do the same as ModuleCollection,
        but we also schedule the modules to run in an asyncio Task.

        This allows modules to start when the event loop starts,
        and it also allows them to generate events when they encounter them.

        :param module: Module to load
        :type module: BaseModule
        :return: Module loaded
        :rtype: BaseModule
        """

        # Load the module:

        super().load_module(module)

        # Schedule the module to run as a Task:

        task = self.event_loop.create_task(self.run_module(module))

        # Add the task to the task list:

        temp = list(self.tasks)

        temp.append(task)

        self.tasks = tuple(temp)

        # Return the module:

        return module

    async def run_module(self, module: BaseIO):
        """
        Runs the given module.

        We only care about capturing read events from the modules.
        We await until we get a return value,
        and then we add it to our queue.

        :param module: Module to work with
        :type module: BaseIO
        """

        # Start up the module:

        await self.start_module(module)

        # Run everything in try, so we can stop if canceled...

        try:

            # Sanity check passed! Loop until we stop...

            while self.running and module.running:

                # Get event from module:

                event = await module.get()

                # Add the event to the queue:

                await self.queue.put(event)

        except asyncio.CancelledError:

            # We have been cancelled!

            raise

        finally:

            # Stop the module in question:

            if module.running:

                await self.stop_module(module)
