"""
Miscellaneous components used by yap-midi.
"""

import asyncio

from typing import Any
from time import perf_counter_ns

from ymidi.errors import ModuleLoadException, ModuleStartException, ModuleStopException, ModuleUnloadException

# Function that yapmidi uses to get time:

ytime = perf_counter_ns


def write_varlen(num: int) -> bytes:
    """
    Converts an integer into a collection of bytes.

    We return the converted bytes after the operation is complete.

    :param num: Number to encode
    :type num: int
    :return: Bytes of encoded data
    :rtype: bytes
    """
                
    bytes = []
        
    while num:
                        
        bytes.append(num & 0x7f)
            
        num >>= 7

    if bytes:
            
        bytes.reverse()
            
        for i in range(len(bytes) - 1):
                
            bytes[i] |= 0x80
                
        return bytes

    return [0]


def de_to_ms(self, delta: int, division: int, mpb: int) -> int:
    """
    Converts the given delta time into microseconds.

    We require the byte division and tempo in microseconds per beat(MPB) note for this operation.

    :param delta: Delta time to convert
    :type delta: int
    :param division: Division of the delta time
    :type division: int
    :param tempo : Temp in MPB
    :return: Time in milliseconds
    :rtype: int
    """
    
    return delta * (mpb / division)


def ms_to_de(milli: int, division: int, tempo: int) -> int:
    """
    Converts the given microseconds into delta time.
    
    We require the byte division and tempo in milliseconds per beat(MPB) for this operation.

    :param milli: Millisecond time to convert
    :type milli: int
    :param division: Division of delta time
    :type division: int
    :param tempo: Temp in MPB
    :type tempo: int
    :return: Time in delta time(or number of ticks)
    :rtype: int
    """

    return (milli * division) / tempo


def mpb_to_bpm(mpq: int, denom: int=4) -> int:
    """
    Converts the microseconds per beat into beats per minute(BPM).

    We optionally require the denominator of the time signature.
    Because most of the time this is 4, we default to 4.

    :param mpq: Microseconds per beat
    :type mpq: int
    :param denom: Time signature denominator
    :type denom: int
    :return: Tempo in BPM
    :rtype: int
    """

    return (60000000 / mpq) * (denom/4)


def bpm_to_mpb(bpm: int, denom: int=4) -> int:
    """
    Converts Beats Per Minute(BPM) to milliseconds per beat(MPB).

    We optionally require the denominator of the time signature.
    Because most of the time this is 4, we default to 4.

    :param bpm: BPM
    :type bpm: int
    :param denom: Time signature denominator, defaults to 4
    :type denom: int, optional
    :return: Milliseconds per beat
    :rtype: int
    """

    return (60000000 * denom) / (4 * bpm)


class BaseModule(object):
    """
    BaseModule - Class all yap-midi modules MUST inherit!

    A 'module' is a modular component that is designed
    to be loaded into yap-midi components.
    Some examples of this are IO modules,
    and event handlers.

    This class implements some common features that modules may find helpful.
    We also define some useful functionality for developers
    that allow modules to be identified.

    A module has these states:

                      +<------------------------------<+                                 
    Created -> Loaded +> Started -> Running -> Stopped +> Unloaded

    * Created - Module is instantiated
    * Loaded - Module is loaded into a collection, relevant load code is ran
    * Started - Module is started, relevant start code is ran 
    * Running - Module is running and working with data given to it
    * Stopped - Module is stopped, relevant stop code is ran and module is no longer working with data
    * Unloaded - Module is unloaded, relevant unload code is ran

    This state chain shows each position a module can be in.
    Each state leads to the other, and the chain restarts if the module is unloaded.
    The exception to this rule is the stopped state,
    which can lead back to the started state if the module is started again.

    These states are reached by calling the relevant methods
    for the given module.
    These methods are usually called by some high-level class,
    such as IOCollection, but the developer can certainly call
    these methods manually.

    Sub-classes can and should add functionality to this class.
    
    TODO: Fix docstrings for this class!
    """

    NAME = "BaseModule"  # Absolute name of the module

    def __init__(self, name=''):

        self.name = name  # Friendly name of the module, changes per module, defined by the user
        self.running = False  # Value determining if we are running
        self.collection: Any = None  # Instance of the ModuleCollection we are apart of

    async def start(self):
        """
        Method called when this IO module is started.

        This method is usually invoked by the ModuleCollection class,
        but this can defiantly be invoked by a user,
        or even this module itself when used discretely!

        Developers can really put anything they want in here,
        but it is recommended to start or invoke any components 
        that are necessary for this module's operation,
        as it is very likely that this module will start working with MIDI data soon!
        """

        pass

    async def stop(self):
        """
        Method called when this IO module is stopped.

        This method, like start(), is usually invoked by the ModuleCollection class,
        but this can defiantly be invoked by a user,
        or even this module itself when used discretely!

        Developers can really put anything they want in here,
        but it is recommended to stop all components in use by this module,
        as it will stop working with MIDI data soon.

        Do not do anything too permanint!
        This module may be started again at a later date,
        in the case of a module restart operation.
        Again, do do anything crazy permanint,
        just stop all components, ideally in a way that can be started again.
        """

        pass

    def load(self):
        """
        Method called when this IO module is loaded.

        This method is invoked when the module is loaded into a ModuleCollection class.
        THIS DOES NOT MEAN THE MODULE SHOULD GET READY FOR USE!
        That is the job of the start() method.
        Just because a module is loaded does not mean that it will be used.

        It is recommended to put basic startup code here,
        or define some parameters that change at load time.
        You should NOT start any major components in use
        until the start() method is called!

        Do note, this method is NOT asynchronous!
        This is synchronous code designed to be ran in synchronous contexts.
        This allows for users to configure this module before the asyncio event loop starts.
        """

        pass

    def unload(self):
        """
        Method called when this IO module is unloaded.

        This method is invoked when the module is unloaded from a ModuleCollection class.
        When this method is called,
        it is reasonable to assume that this module is not going to be used again.
        IO modules can use this a a sign that their work is done.

        It is recommended to make any final, permanint changes once this method is called.

        Do note, like load(), this method is NOT asynchronous!
        This is synchronous code designed to be ran in synchronous contexts.
        This allows for users to configure this module before the asyncio event loop starts.
        """

        pass


class ModuleCollection(object):
    """
    ModuleCollection - Class all module collections MUST inherit!

    A ModuleCollection is a class that manager multiple modules,
    usually of a certain kind, for the user.
    This class does not offer entry points into said modules,
    that is the job of the child class to implement functionality.
    
    Instead, we offer methods to alter these modules,
    and automatically handle them so the implementing classes don't have too.
    This includes managing the module state,
    and calling the correct functions when necessary.

    We keep the list of modules in a tuple,
    for memory and performance reasons.
    We implement list-like features,
    allowing users to iterate over the loaded modules
    and manipulate them.
    Keep in mind, the structure responsible for housing these modules is a tuple.
    This means that with each change,
    an entirely new tuple must be created.
    The tuple format allows for a low memory footprint,
    and allows for items to be accessed quickly,
    which is very important for asynchronous high speed situations like MIDI processing.
    However, altering the structure of modules is a very slow process.
    It is recommended to load all necessary modules into this collection
    before MIDI data exchange occurs,
    otherwise the process of creating an entirely new tuple could greatly impact performance.

    It can be safely assumed that all methods defined here WILL
    be present in the final class that inherits us.

    Like other components,
    we work asynchronously which allows for 
    multiple modules to be worked with at once.
    We work with the low-level asyncio event loop,
    and offer methods to alter it easily.
    Because of our asyncio backend,
    we provide methods to run code synchronously,
    and in another thread.
    TODO: Check out this list!
    - Starting event loop synchronously!
    - Threaded event loop invoking
    - TESTING!
    - List-like features
    - Put name of master class in docstrings 
    """

    def __init__(self, event_loop=None, module_type=None) -> None:

        # Module storage component
        self.modules = ()
        # Event loop in use. if not provided, then one will be created
        self.event_loop: asyncio.AbstractEventLoop = event_loop if event_loop is not None else asyncio.get_event_loop()
        self.start_tasks = []  # Module start tasks

        self.module_type = object if module_type is None else module_type  # Module type to use, superclass if not specified
        self.running = False  # Value determining if we are running
        self.num_loaded = 0  # Number of modules currently loaded
        self.max_loaded = 0  # Max number of modules loaded

    def load_module(self, module: BaseModule) -> BaseModule:
        """
        Adds the given module to the collection.

        We ensure that the 'load' method of the module is called,
        and that no exceptions are encountered.
        If we do encounter an exception,
        then we will not load this module!

        We also schedule this handler to be started at a later date via tasks.
        Once this collection is started,
        then all event handlers will have their start() methods called.
        This occurs even while the event loop is running,
        allowing handlers to be added during runtime.

        We also return the instance of the module we loaded.

        :param module: IO Module to add
        :type module: BaseModule
        :return: Module we loaded
        :rtype: BaseModule
        """

        # Do a check to ensure the module is valid:

        if not isinstance(module, self.module_type):

            # Invalid module!

            raise TypeError("Invalid module! MUST inherit {}!".format(self.module_type))

        # Attach ourselves to the module:

        module.collection = self

        # We passed the check, let's run the load method:

        try:

            module.load()

        except Exception as e:

            # Load error occurred! Raise a yap-midi exception!

            raise ModuleLoadException("Module load() method failed! Not loading: {}".format(module.name), e)

        # Add the module to our collection:

        self._load_module(module)

        # Schedule the module's start() method:

        self.start_tasks.append(self.event_loop.create_task(self.run_module(module)))

        # Finally, return the module:

        return module

    def unload_module(self, module: BaseModule) -> BaseModule:
        """
        Removes the given module from the collection.

        We ensure that the stop() and unload() methods are called as appropriate.
        if we do encounter an exception,
        then the module will be forcefully unloaded,
        and no further methods(if any) will be called.

        We first call the stop() method if the module is running,
        and then finally the unload() method.
        After these methods do their work
        (Or if an exception is encountered),
        then we unload the module from the collection.

        We also return a copy of the module we unloaded.

        :param module: Module to unload
        :type module: BaseModule
        :return: Module we unloaded
        :rtype: BaseModule
        """

        # Stop the module if necessary:

        if module.running:

            # Stop the module, call the stop() method:

            self.event_loop.run_until_complete(self.stop_module(module))

        # Now, run the unload method:

        try:

            module.unload()

        except Exception as e:

            # Raise an exception of our own:

            raise ModuleUnloadException("Module failed to unload! Unloading: {}".format(module.name), e)

        # Unload the module:

        self._unload_module(module)

        # Return the module:

        return module

    async def stop_module(self, module: BaseModule) -> BaseModule:
        """
        Stops the given module.
        
        This is done by calling the module's stop() method.
        We also return a copy of the module we worked with.

        :param module: Module to stop
        :type module: BaseIO
        :return: Module we stopped
        :rtype: BaseIO
        :raise: ModuleStopException: If the module stop() method fails
        """

        # Call the stop method:

        try:

            await module.stop()

        except Exception as e:

            # Raise an exception:

            self._unload_module(module)

            raise ModuleStopException("module stop() method failed! Unloading: {}".format(module.name), e)

        # Alter the running status:

        module.running = False

        # Return the module:

        return module

    async def start_module(self, module: BaseModule) -> BaseModule:
        """
        Starts the given module.

        This is done by calling the start() method of the module.
        We also return a copy of the module we worked with.

        If this module fails to start,
        then it will automatically removed!

        :param module: Module to start
        :type module: BaseIO
        :return: Module we started
        :rtype: BaseIO
        """

        # Call the start method:

        try:

            await module.start()

        except Exception as e:

            # Module failed to start! Unload it...

            self._unload_module(module)

            # Raise an exception:

            raise ModuleStartException("Module start() method failed! Unloading: {}".format(module.name), e)

        # Alter the running status:

        module.running = True

        # Return the module:

        return module

    async def restart_module(self, module: BaseModule) -> BaseModule:
        """
        Restarts the given module.

        This is done by calling the start() and stop()
        methods of the module in question.
        The module MUST be in a running position to start!
        We also return the module we restarted.

        If the module fails to start or stop,
        then the module will be forcefully unloaded!

        :param module: Module to restart
        :type module: BaseModule
        :return: The module we restarted
        :rtype: BaseModule
        """

        # Stop the module

        await self.stop_module(module)

        # Start the module:

        await self.start_module(module)

        # Return the module in question:

        return module

    async def start(self):
        """
        Method used to start this ModuleCollection.

        We set our running status,
        and submits the run() coroutine to the event loop.

        This method is designed to be ran from asynchronous code,
        usually the TODO: Put masterclass name here
        will invoke this method.

        Sub-classes should put starter code here to start their relevant components.
        This usually involves starting all loaded modules.
        """

        # Set our runing status:

        self.running = True

    async def stop(self):
        """
        Method used to stop this ModuleCollection.

        We set our running status,
        as well as cancel the run() coroutene.

        Again, this method is designed to be ran from asynchronous code,
        usually the TODO: Put masterclass name here
        will invoke this method.

        Sub-classes should put stop code here to end their relevant components.
        This usually involves stopping all loaded modules.
        """

        # Set our running status:

        self.running = False

    async def run_module(self, module: BaseModule):
        """
        Runs this module, always will be in a task.

        This is the method that gets scheduled to run
        when the module is loaded.
        Usually, this only starts the module and quits.
        However, the developer can add functionality
        that works with this module in another way.

        :param module: Module to work with
        :type module: BaseModule
        """

        # Just start the module:

        await self.start_module(module)

    def _load_module(self, mod: BaseModule):
        """
        Adds the module to our collection. 

        This low-level method is not intended to
        be worked with by end users!

        :param mod: Module to add
        :type mod: BaseModule
        """

        # Create the data to be stored:

        temp = (mod,)

        # Add the module to the collection:

        self.modules = self.modules + temp

        # Update our stats:

        self.max_loaded += 1
        self.num_loaded += 1

        # Attach the collection to the module:

        mod.collection = self

    def _unload_module(self, mod: BaseModule):
        """
        Low-level method for unloading modules from the list.

        We do not call any methods or work with the module in any way
        other than removing it from the data structure.

        We are not meant to be called directly!
        This method should only be called by high-level
        methods of IOCollection.

        :param mod: The module in question to remove
        :type mod: BaseModule
        :param key: Key of the module to remove
        :type key: str
        """

        # Convert the tuple into a list:

        temp = list(self.modules)

        # Remove the offending module:

        temp.remove(mod)

        # Set our list:

        self.modules = tuple(temp)

        # Update our stats:

        self.num_loaded -= 1

        # Remove ourselves from the module:

        mod.collection = None
