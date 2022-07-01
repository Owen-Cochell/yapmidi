"""
Components that house MIDI events and other misc. data, 
"""

import asyncio

from collections import defaultdict

from ymidi.events.base import BaseEvent
from ymidi.handlers.maps import DEFAULT_TRACK_IN, DEFAULT_TRACK_OUT
from ymidi.misc import de_to_ms, ms_to_de, bpm_to_mpb, mpb_to_bpm


class BaseContainer(list):
    """
    BaseContainer - A class all containers should inherit!

    The main functionality here is defining the input and output
    HandlerCollections, which define how we change the state of the collection
    based upon events coming in or out.

    For example, we may want to set the track name if we receive a TrackEvent.
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

    def __init__(self, load_default_in: bool=True, load_default_out: bool=True) -> None:

        self.in_hands = defaultdict(list)
        self.out_hands = defaultdict(list)

        # Check if we should load the default handlers:

        if load_default_in:

            self.in_hands.update(DEFAULT_TRACK_IN)

        if load_default_out:

            self.out_hands.update(DEFAULT_TRACK_OUT)


class Pattern(BaseContainer):
    """
    A collection of tracks.

    We contain a list of tracks that contain MIDI events.
    We keep track(haha) of statistics and data related to the
    MIDI data we contain.
    We do this by handling Meta events and yap-events.

    We also support playback of the MIDI data.
    This includes ALL MIDI track types,
    and supports tracks that are playing at different speeds.
    """

    def __init__(self, load_default_in: bool = True, load_default_out: bool = True) -> None:

        super().__init__(load_default_in, load_default_out)

        self._msb = 0  # Number of microseconds per beat

        self.num_tracks = 0  # Number of tracks we have registered
        self.track_index = 0  # Keeps track of the track we are on

    @property
    def msb(self) -> int:
        """
        Gets the microseconds per beat.

        :return: Microseconds per beat
        :rtype: int
        """
        
        return self._msb

    @msb.setter
    def msb(self, value: int):
        """
        Sets the microseconds per beat.
        
        This not only sets the attribute on this class,
        but also sets this value in each of the tracks attached to this Pattern.

        :param value: Value to set
        :type value: int
        """
        
        self._msb = value
        
        for track in self:
            
            track.msb = value

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

        for func in self.in_hands[event.statusmsg]:

            func(self, event)


class Track(BaseContainer):
    """
    A track of MIDI events.

    We offer some useful helper methods that make
    altering and adding MIDI events a relatively painless affair.

    We inherit the default python list,
    so we support all list operations.
    """

    def __init__(self, load_default_in: bool=True, load_default_out: bool=True):

        super().__init__(load_default_in=load_default_in, load_default_out=load_default_out)

        self.name = ''  # Name of the track
        self.tempo = 120  # Tempo in Beats Per Minute
        self.instrument = ''  # Name of the instrument for this track

        self.index = 0  # Index we are on
        self.start_time = 0  # Time we have started on, we use the ymidi timer for this
        self.timesig_num = 4  # Numerator of the time signature
        self.timesig_den  = 4  # Denominator of the time signature
        self.msb = bpm_to_mpb(self.tempo, denom=self.timesig_den)  # number of microseconds per beat

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

        for func in self.out_hands[event.statusmsg]:

            func(self, event)

        # Finally, return the event:

        return event

    async def time_get(self) -> BaseEvent:
        """
        Gets an event from the track,
        but waits to return the event until it is time for the event to be returned.

        This allows you to play a track in real time!
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

        time_sleep = de_to_ms(event.delta)

        # Wait for a given time:

        if time_sleep != 0: 

            await asyncio.sleep(time_sleep)

        # Return the event:

        return event

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

        for hand in self.in_hands[value.statusmsg]:

            hand(self, value)

        # Call the super method:

        super().__setitem__(key, value)
