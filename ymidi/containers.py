"""
Components that house MIDI events and other misc. data, 
"""

import asyncio

from collections import defaultdict, UserList
from operator import index
from typing import Any

from ymidi.events.base import BaseEvent
from ymidi.handlers.maps import DEFAULT_TRACK_IN, DEFAULT_TRACK_OUT, DEFAULT_PATTERN_IN, DEFAULT_PATTERN_OUT, GLOBAL, TRACK
from ymidi.handlers.track import global_tempo
from ymidi.misc import de_to_ms, ms_to_de, bpm_to_mpb, mpb_to_bpm, ytime
from ymidi.constants import TEMPO_SET


class BaseContainer(UserList):
    """
    BaseContainer - A class all containers should inherit!

    The main functionality here is defining the input and output
    HandlerCollections, which define how we change the state of the collection
    based upon events coming in or out.

    For example, we may want to set the track name if we receive a TrackName event.
    We would add a handler to the input collection to set the name the second we receive the event.
    However, if we receive a SetTempo event, we would want to change the tempo when we we encounter it
    and remove it from the collection. If we interpret the SetTempo event as it enters the collection,
    then we will set the tempo to a value that may not be accurate at the start of the track.

    This system also allows users to remove functionality from the track.
    For example, if you want to ignore SetTempo events, then you can clear the handler
    assigned to the event. This means that any tempo changes will be ignored,
    and the tempo of the track will not be changed.

    The output handlers are only used if this track is playing back events.
    These handlers should be a single function that takes two arguments,
    the container instance, and the event to be handled.
    
    If you do not wish to load the default track handlers,
    then you can pass False to 'load_default_in' to not load in handlers,
    and 'load_default_out' to not load out handlers.
    """

    def __init__(self, default_in: dict, default_out: dict, load_default_in: bool=True, load_default_out: bool=True) -> None:

        super().__init__()

        self.in_hands = defaultdict(list)
        self.out_hands = defaultdict(list)

        self.index = 0  # Index we are on
        self.start_time = 0  # Start time

        # Check if we should load the default handlers:

        if load_default_in:

            self.in_hands.update(default_in)

        if load_default_out:

            self.out_hands.update(default_out)

    def start_playback(self):
        """
        Prepares this container for playback.

        This function should be called when users
        are wishing to playback events in this container.
        Calling this function will tell the container
        that playback should be starting now,
        so extracting values from this container should begin soon!
        Otherwise, the container will rapidally return events that were due in the past.
        For example, if you wait 5 seconds to extarct events,
        then events that occur before the 5 second mark will immediatly be
        returned each time the 'get_time()' method is acalled, as the container will be attempting to catch up.

        The implementation of this method will differ per each container.
        """

        raise NotImplementedError("Must be implemented in child class!")

    def append(self, event: BaseEvent):
        """
        Appends an event to this track.

        We do the exact same thing as conventional list objects,
        except that we run the event through the event handlers.

        :param event: Event to append
        :type event: BaseEvent
        """

        # Run thorugh the events:

        print("in append")

        self._handle_event(event, len(self))

        # Call the super method:

        return super().append(event)

    def insert(self, i: int, item: Any):
        """
        Inserts the given event into the track.

        We do the exact same thing as conventional list objects,
        except that we run the event through the event handlers.

        :param i: Index to insert at
        :type i: int
        :param item: Event to insert
        :type item: Any
        """

        print("in insert")

        self._handle_event(item, i)

        # Call the super method

        return super().insert(i, item)

    def __setitem__(self, key: int, value: BaseEvent):
        """
        Sets the given event at a key.

        We also call the relevant in handlers for this event.

        :param key: Key of the value to set
        :type key: int
        :param value: Value to set
        :type value: BaseEvent
        """

        # Run the event through the handlers:

        print("IN set")
        print("Key : {}".format(key))
        print("Value: {}".format(value))

        self._handle_event(value, index)

        # Call the super method:

        return super().__setitem__(key, value)

    def _handle_event(self, event: Any, index: int):
        """
        Handles the given event.

        We expect an event to process,
        and an index that the event will be kept at.

        :param event: Event to handle
        :type event: Any
        """

        for hand in (self.in_hands[event.statusmsg] + self.in_hands[GLOBAL]):

            print("Handling: {}".format(hand))

            if hand(self, event, index):

                break


class Pattern(BaseContainer):
    """
    A collection of tracks.

    We contain a list of tracks that contain MIDI events.
    We keep track(haha) of statistics and data related to the
    MIDI data we contain.
    We do this by handling Meta events and yap-events.
    If you want to handle tracks coming in,
    then you should use the TRACK constant to do so.
    This handler will run determine if we are handling tracks,
    and run them through the track handlers ONLY!

    We also support playback of the MIDI data.
    This includes ALL MIDI track types,
    and supports tracks that are playing at different speeds.
    """

    statusmsg = TRACK

    def __init__(self, division: int=48, load_default_in: bool = True, load_default_out: bool = True) -> None:

        super().__init__(DEFAULT_PATTERN_IN, DEFAULT_PATTERN_OUT, load_default_in, load_default_out)

        self._division = division

        self.num_tracks = 0  # Number of tracks we have registered
        self.track_index = 0  # Keeps track of the track we are on
        self._format = 0  # Format of this pattern, should be 0, 1, 2

    @property
    def division(self) -> int:
        """
        Gets the time division, which is the number of ticks per beat.

        :return: Microseconds per beat
        :rtype: int
        """

        return self._division

    @division.setter
    def division(self, value: int):
        """
        Sets the number of ticks per beat.

        This not only sets the attribute on this class,
        but also sets this value in each of the tracks attached to this Pattern.

        :param value: Value to set
        :type value: int
        """

        self._division = value

        for track in self:

            track.divison = value

    @property
    def format(self) -> int:
        """
        Returns the format of this pattern.

        :return: Pattern format
        :rtype: int
        """

        return self._format

    @division.setter
    def format(self, format: int):
        """
        Sets the format of the pattern.

        If we are format 0 or 1,
        and we are loading default handlers,
        then we also add the 'global_tempo' track handler.

        :param format: New format of this pattern.
        :type format: int
        """

        self._format = format

        if self.load_default and self._format in (0,1):

            # Add the 'global_tempo' handler:

            self.in_hands[TEMPO_SET].append(global_tempo)

    def submit_event(self, event: BaseEvent):
        """
        Submits the given event to the Pattern.

        This method will send the event though the in pattern handlers
        bound to this object.
        This means that events can be auto-sorted and managed(if the required pattern handlers are loaded), so you don't have to.
        For example, events that are meant for a given track will be sorted
        into their respective track(given that the valid builtin/meta events are present).

        :param event: Event to add
        :type event: BaseEvent
        """

        # Run the event though the handlers:

        for func in (self.in_hands[event.statusmsg] + self.in_hands[GLOBAL]):

            func(self, event)

    def start_playback(self, index: int = 0, time: int = None):
        """
        Gets all attached tracks ready for playback.
        """

        for track in self:

            track.start_playback(index, time)

    def get(self) -> BaseEvent:
        """
        Gets the next event in this pattern.

        We get the newest event from the tracks,
        and run this event through the output handlers.

        We require the 'event_tick' track handler to be loaded.
        TODO: There is a way to do this without the track handler, implement it!

        :return: Event we encountered
        :rtype: BaseEvent
        """

        first_event, track = self._get_newest()

        # Return our first event:

        return self[track].get()

    async def time_get(self) -> BaseEvent:
        """
        Gets an event from the from the tracks, but waits
        until the newest event is ready to be returned.

        This means that events from multiple tracks can
        be played back accurately.
        We find the earliest event in all tracks,
        and wait until it is ready to be returned.

        We need the 'start_playback()' method to be called,
        otherwise the playback will not be accurate!

        :return: Next event in all tracks
        :rtype: BaseEvent
        """

        # Get the track to work with:

        first_event, track = self._get_newest()

        # Run the time_get method:
  
        return await self[track].time_get()

    def _get_newest(self) -> BaseEvent:
        """
        Gets the newest event from the all tracks.

        We return the newest event and the track it came from.

        :return: Newest event
        :rtype: BaseEvent
        """

        # Get each event and compare the ticks:

        first_event = None
        ticks = -1

        for track, event in enumerate(self):

            if ticks < 0 or event.tick <= ticks:

                # Event comes sooner, log it:

                first_event = event
                ticks = event.tick

        return first_event, track


class Track(BaseContainer):
    """
    A track of MIDI events.

    We offer some useful helper methods that make
    altering and adding MIDI events a relatively painless affair.

    We inherit the default python list,
    so we support all list operations.
    """

    def __init__(self, load_default_in: bool=True, load_default_out: bool=True):

        super().__init__(DEFAULT_TRACK_IN, DEFAULT_TRACK_OUT, load_default_in=load_default_in, load_default_out=load_default_out)

        self.name = ''  # Name of the track
        self._tempo = 120  # Tempo in Beats Per Minute
        self.instrument = ''  # Name of the instrument for this track

        self.index = 0  # Index we are on
        self.start_time = 0  # Time we have started on, we use the ymidi timer for this
        self.last_time = 0  # Time of the last event
        self.timesig_num = 4  # Numerator of the time signature
        self.timesig_den  = 4  # Denominator of the time signature
        self._mpb = bpm_to_mpb(self.tempo, denom=self.timesig_den)  # number of microseconds per beat
        self.division = 48  # Division of this track

    @property
    def tempo(self) -> int:
        """
        Returns the tempo in Beats Per Minute(BPM).
        """

        return self._tempo

    @tempo.setter
    def tempo(self, tempo: int):
        """
        Sets the tempo in Beats Per Minute(BPM).

        We also convert this value internally
        into milliseconds per beat.
        This is important for certain MIDI time operations.

        :param tempo: Tempo in BPM
        :type tempo: int
        """

        self._tempo = tempo
        self._mpb = bpm_to_mpb(tempo, self.timesig_den)

    @property
    def mpb(self) -> int:
        """
        Returns the number microseconds per beat(MPB).

        :return: MPB
        :rtype: int
        """

        return self._mpb

    @tempo.setter
    def mpb(self, mpb: int):
        """
        Sets the microseconds per beat(MPB) of this track.

        We also update the tempo in beats per minute(BPM).

        :param msb: MPB
        :type msb: int
        """

        self._mpb = mpb
        self._tempo = mpb_to_bpm(mpb, self.timesig_den)

    def start_playback(self, index: int=0, time:int = None):
        """
        Prepares this container for playback.

        We set the index to zero and set the start time.
        This method can also be used to reset the playback to the start!
        You can also manually specify the index and time values to be set.

        After this function is called,
        users should start extracting values from the collection immediatly!
        """

        # Set the index:

        self.index = index

        # Set the start time:

        self.start_time = ytime() if time is None else time

        # Set the last time to now as well:

        self.last_time = self.start_time

    def rehandle(self, hands=None):
        """
        Runs all registered events through the event handlers.
        We by default run them through the in handlers.
        You can specify they type by using the 'hands' parameter,
        just pass 'out_hands'.
        However, you should probably just stick to in handlers.

        This is great if we need to update values that
        relay on previous events if an event gets inserted.
        This operation can take a long time depending on 
        how many events and track handlers are loaded.

        This method can be called manually,
        but some track handlers can invoke this process manually.
        """

        if hands is None:

            hands = self.in_hands

        for index, event in enumerate(self):

            # Get all handlers for this event:

            self._handle_event(event, index)

    def get(self) -> BaseEvent:
        """
        Gets the next event from the container.

        We also send our events though the track handlers.

        :return: The next handler in the container
        :rtype: BaseEvent
        """

        # Get the event:

        event = self[self.index]

        # Run the event though the handlers:

        for func in (self.out_hands[event.statusmsg] + self.out_hands[GLOBAL]):

            func(self, event, self.index)

        # Increment the index:

        self.index += 1

        # Finally, return the event:

        return event

    async def time_get(self) -> BaseEvent:
        """
        Gets an event from the track,
        but does not do so until it is time for the event to be returned.

        This may seem simular to 'wait_get()',
        except that we use the absolue time of the event.
        For example, if you called this function after waiting 3 seconds,
        then the three seconds will be subtracted from the current event's delta time.
        This is useful if you canceled the 'wait_get()' method,
        or if will not be calling this event at the exact start of the delta wait time
        (This is what the Pattern class does!).

        This method requires the 'start_playback()' method to be called,
        otherwise playback may not be accurate.

        :return: Event to be returned
        :rtype: BaseEvent
        """

        # Determine the wait time:

        event = self[self.index]

        time_sleep = ((de_to_ms(event.delta, self.division, self._mpb) + self.last_time) - ytime()) - 1000

        print("Sleeping for: {}".format(time_sleep))
        print("Seconds: {}".format(time_sleep / 1000000))
        print("Time delta seconds: {}".format(event.delta_time / 1000000))

        # Wait for a given time:

        if time_sleep > 0:

            await asyncio.sleep(time_sleep / 1000000)

        # Set the last time:

        self.last_time = ytime()

        # Return the event:

        return self.get()

    async def wait_get(self) -> BaseEvent:
        """
        Gets an event from the track,
        but waits the entire delta time before the event is returned.

        This allows you to wait the whole delay of an event before recieveing it.
        We calculate the time to wait based upon the division of the track,
        the current tempo of the track, and the delta time of the event.

        This function should be awaited.
        We use asyncio methods to wait asynchronously.
        To ensure that playback is accurate,
        it is recommended to use the default container handlers,
        as they will alter the state of this container based upon the events we encounter.
        For example, if we encounter a SetTempo event, then we will change the tempo of this container.
        If this handler is not present, then the tempo will not change.

        :return: Next event in the container
        :rtype: BaseEvent
        """

        # Get the event to process:

        event = self[self.index]

        # Determine the time to sleep:

        time_sleep = de_to_ms(event.delta, self.division, self._mpb)
        print("Sleeping for: {}".format(time_sleep))
        print("Seconds: {}".format(time_sleep / 1000000))
        print("Time delta seconds: {}".format(event.delta_time / 1000000))

        # Wait for a given time:

        if time_sleep > 0: 

            await asyncio.sleep(time_sleep / 1000000)

        # Return the event:

        return self.get()
