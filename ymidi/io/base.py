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

from __future__ import annotations

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

    def __init__(self, proto: BaseProtocol, decoder: BaseDecoder, name: str = "") -> None:

        super().__init__(name=name)

        self.proto: BaseProtocol = proto  # Protocol object in use
        self.decoder: BaseDecoder = decoder  # Decoder in use

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

    async def start(self):
        """
        Starts this IO module.

        All child IO modules should call this function!
        We make sure the protocol object is properly started.
        """

        self.proto.start()

    async def stop(self):
        """
        Stops this IO module.

        All child IO modules should call this function!
        We make sure the protocol object is stopped correctly.
        """

        self.proto.stop()

    def has_events() -> bool:
        """
        Determines if there are any more events to return.

        This operation can greatly differ depending on the Io module,
        so the dirty details are left up to the child class.

        This should return True if there are more events to return,
        and False if there are no more events to return.

        :return: Boolean determining if there are events to return
        :rtype: bool
        """

        raise NotImplementedError("Must be overridden in child class!")


class NullIO(BaseIO):
    """
    NullIO - Does nothing!

    As per the name, we input nothing and output nothing.
    This is the default IO module,
    as it ensures nothing unexpected happens.
    """

    NAME = "NullIO"

    def __init__(self) -> None:
        super().__init__(BaseProtocol, None, name="NullIO")

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

    def has_events() -> bool:
        """
        Because we will never return anything,
        we always return False.

        :return: Always returns False
        :rtype: bool
        """

        return False


class EchoIO(BaseIO):
    """
    EchoIO - Adds inputted events to our output queue.

    As we receive inputs,
    we output them when requested.
    """

    def __init__(self) -> None:

        super().__init__(BaseProtocol, None, name="EchoIO")

        self.queue = asyncio.queues.Queue()

    async def get(self) -> BaseEvent:
        """
        Returns echoed content from our queue.

        :return: Event from queue
        :rtype: BaseEvent
        """

        return await self.queue.get()

    async def put(self, event: BaseEvent):
        """
        Put the event into our queue.

        :param event: Event to put into our queue
        :type event: BaseEvent
        """

        await self.queue.put(event)


class IOCollection(ModuleCollection):
    """
    IOCollection - Manages IO modules!

    This class manages, organizes, and works with IO modules.
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
    Advanced components will bypass these methods and access the queue directly.

    This class supports auto removal!
    For example, if an IO module has no more events,
    then it can be automatically removed from the collection.
    This is determined by calling the 'has_events()' method.
    If an IO module is done, 
    then it will be automatically stopped and unloaded.
    This is great for getting rid of tasks that are doing nothing!

    TODO: Check out this list!
    - Implement better queue entry points
    - Some runner system for multi-threaded code?
    - TESTING!
    """

    def __init__(self, event_loop=None, auto_remove: bool = True) -> None:

        super().__init__(event_loop, BaseIO)

        print("RUNNING: {}".format(self.running))

        self.queue = asyncio.queues.Queue()  # Output queue that holds events

        self.modules: Tuple[BaseIO, ...] = ()
        self.auto_remove = auto_remove  # Determines if we should auto-remove modules

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

        We utilize the event loop to run the async code.

        :return: BaseEvent object retrieved from the queue.
        :rtype: BaseEvent
        """

        # Put the get method in the event loop:

        return self.event_loop.run_until_complete(self.get())

    def sync_put(self, event: BaseEvent):
        """
        Puts the given event into the event queue.

        This allows for Non-asynchronous code to interact with the IO queue.

        Like sync_get(), we utilize the event loop to run the async code.

        :param event: BaseEvent object to add to the queue
        :type event: BaseEvent
        """

        # Run put() method in event loop:

        return self.event_loop.run_until_complete(self.put(event))

    async def run_module(self, module: BaseIO):
        """
        Runs the given module.

        We only care about capturing read events from the modules.
        We await until we get a return value,
        and then we add it to our queue.

        :param module: Module to work with
        :type module: BaseIO
        """

        print("BAD run function")

        # Start up the module:

        await self.start_module(module)

        # Run everything in try, so we can stop if canceled...

        try:

            # Sanity check passed! Loop until we stop...

            while self.running and module.running and (not self.auto_remove or module.has_events()):

                # Get event from module:

                event = await module.get()

                # Add the event to the queue:

                await self.queue.put(event)

        except asyncio.CancelledError:

            # We have been cancelled!

            pass

        finally:

            # Stop the module in question:

            if module.running:

                await self.stop_module(module)


class ChainIO(BaseIO, IOCollection):
    """
    ChainIO - Allows for IO modules to utilize other IO modules.

    This allows for IO modules to be recursively nested within each other.
    For example, an IO module could take inputs from multiple modules,
    and do some operations on them.

    We inherit IOCollection, so we support all it's methods and features.
    We change a few things, such as redefining get() to get get_chain()
    which will get events from the chained modules.

    This class is not intended to be used directly.
    Instead, this class is here to be inherited by other IO modules.
    You can use this class directly,
    and it will work as advertised.
    """

    def __init__(self, proto: BaseProtocol, decoder: BaseDecoder, name: str = "", auto_remove: bool = True) -> None:

        super().__init__(proto, decoder, name)

        self.auto_remove = auto_remove

    async def get_chain(self) -> BaseEvent:
        """
        Gets an event from the chained IO modules.

        :return: Event
        :rtype: BaseEvent
        """

        return await super().get()

    async def put_chain(self, event: BaseEvent):
        """
        Puts an event into the chained IO modules.

        :param event: Event to put into chained IO modules
        :type event: BaseEvent
        """

        await super().put(event)


class RouteIO(ChainIO):
    """
    RouteIO - Pulls events from one IO module and puts it in another,
    essentially allowing you to connect IO modules together.

    The purpose of this class is to pull IOModules from our inputs,
    and send the event to our outputs.

    IO modules can be registered as either inputs or outputs.
    The inputs will have 'get()' continuously called.
    The events will be retrieved and will be sent to the output IO modules via 'put()'.

    Calling 'get()' will do this operation each time it is called.
    This is to ensure that the routing will happen all the time
    if this module is attached to an IOCollection.
    'put()' will send the given event to all output IO modules.
    """

    def __init__(self, auto_remove: bool = True) -> None:

        super().__init__(BaseProtocol, None, name="RouteIO", auto_remove=auto_remove)

        self.running = True

        print("Running: {}".format(self.running))

        self.input = []  # List of input modules
        self.output = []  # List of output modules

    def has_events(self) -> bool:
        """
        Determines if we have more events to return.

        We just see if there are any events 
        in our input modules.

        :return: Boolean determining if there are any more events
        :rtype: bool
        """

        for mod in self.input:

            if mod.has_events():

                return True

        return False

    def load_input(self, module: BaseIO):
        """
        Loads an IO module as an input.

        Input modules will have events extracted from them.
        These input modules will also be ran as a task
        under the 'run_module()' method.

        :param module: Module to load
        :type module: BaseIO
        """

        # Run the super load method:

        self.load_module(module)

        self.input.append(module)

    def load_output(self, module: BaseIO):
        """
        Loads an IO module as output.

        Output modules will have events put into them.
        These output modules will NOT be ran as a task,
        and will have events put into them once output modules have events to return.

        :param module: Module to load
        :type module: BaseIO
        """

        # Load the module, but only call the start method!

        self.load_module(module, run_func=self.start_module)

        self.output.append(module)

    async def run_module(self, module: BaseIO):
        """
        Runs the given module.

        We are identical to the 'run_module()' method in the IOCollection,
        except that we pass the event to all output modules.

        :param module: Module to work with
        :type module: BaseIO
        """

        # Start up the module:

        await self.start_module(module)

        # Run everything in try, so we can stop if canceled...

        try:

            # Sanity check passed! Loop until we stop...

            while self.running and module.running and (not self.auto_remove or module.has_events()):

                # Get event from module:

                event = await module.get()

                print("Got event: {}".format(event))

                # Add the event to the queue:

                for mod in self.output:

                    print("Handling event: {}".format(event))

                    await mod.put(event)

            print("No longer running!")

            print(self.running)
            print(module.running)
            print(not self.auto_remove or module.has_events())

        except asyncio.CancelledError:

            # We have been cancelled!

            print("We have been canceled!")

            pass

        except Exception as e:

            print("Exception: {}".format(e))

            raise e

        finally:

            # Stop the module in question:

            print("Stopping module...")

            if module.running:

                await self.stop_module(module)
