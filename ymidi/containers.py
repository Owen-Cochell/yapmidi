"""
Components that house MIDI events and other misc. data, 
"""

import asyncio

from collections import defaultdict, UserList
from typing import Any
from ymidi.errors import StopPlayback

from ymidi.events.base import BaseEvent
from ymidi.events.builtin import StartPattern, StopPattern
from ymidi.events.meta import EndOfTrack
from ymidi.handlers.maps import DEFAULT_TRACK_IN, DEFAULT_TRACK_OUT, DEFAULT_PATTERN_IN, DEFAULT_PATTERN_OUT, GLOBAL, TRACK
from ymidi.misc import de_to_ms, ms_to_de, bpm_to_mpb, mpb_to_bpm, ytime
from ymidi.constants import META, TEMPO_SET, TRACK_END


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

    def __init__(self, default_in: dict, default_out: dict, load_default_in: bool = True, load_default_out: bool = True) -> None:

        super().__init__()

        self.in_hands = defaultdict(list)
        self.out_hands = defaultdict(list)

        self.out_index = 0  # Index we are on
        self.in_index = 0   # In index we are on
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
        Otherwise, the container will rapidly return events that were due in the past.
        For example, if you wait 5 seconds to extract events,
        then events that occur before the 5 second mark will immediately be
        returned each time the 'get_time()' method is called, as the container will be attempting to catch up.

        The implementation of this method will differ per each container.
        """

        raise NotImplementedError("Must be implemented in child class!")

    def submit_event(self, event: BaseEvent, index: int = None):
        """
        Submits the given event to the container.

        This method will send the event though the in pattern handlers
        bound to this object.
        This means that events can be auto-sorted and managed(if the required pattern handlers are loaded), so you don't have to.
        For example, events that are meant for a given track will be sorted
        into their respective track(given that the valid builtin/meta events are present).

        Users can specify the index to insert the event in.
        If this is not specified, then the event will be appended to the end of the list.

        :param event: Event to add
        :type event: BaseEvent
        """

        if index is None:

            index = len(self)

        # Run the event though the handlers:

        self._handle_event(event, index, self.in_hands)

    def _handle_event(self, event: Any, index: int, collec: dict):
        """
        Handles the given event.

        We expect an event to process,
        and an index that the event will be kept at.

        We also need a collection of track handlers to work with.

        :param event: Event to handle
        :type event: Any
        """

        key = event.statusmsg

        if event.statusmsg == META:

            # Working with a meta event, set the key:

            key = event.type

        hands = set(collec[key] + collec[GLOBAL])

        for hand in hands:

            if hand(self, event, index):

                return


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

    def __init__(self, divisions: int = 48, load_default_in: bool = True, load_default_out: bool = True) -> None:

        super().__init__(DEFAULT_PATTERN_IN, DEFAULT_PATTERN_OUT,
                         load_default_in, load_default_out)

        self._divisions = divisions

        self.num_tracks = 0  # Number of tracks we have registered
        self.track_index = 0  # Keeps track of the track we are on
        self.format = 0  # Format of this pattern, should be 0, 1, 2

        self.playing_tracks = []  # List of playing tracks
        self.playing = False  # Boolean determining if we are playing

        self.started = False  # Value determining if we have returned StartPattern()
        self.stopped = False  # Value determining if we have returned StopPattern()

        self.start_pattern = None  # Start Pattern event representing the start of this pattern
        self.stop_pattern = None  # Stop Pattern event representing the end of this pattern

    @property
    def divisions(self) -> int:
        """
        Gets the time divisions, which is the number of ticks per beat.

        :return: Microseconds per beat
        :rtype: int
        """

        return self._divisions

    @divisions.setter
    def divisions(self, value: int):
        """
        Sets the number of ticks per beat.

        This not only sets the attribute on this class,
        but also sets this value in each of the tracks attached to this Pattern.

        :param value: Value to set
        :type value: int
        """

        self._divisions = value

        for track in self:

            track.divisions = value

    def add_track(self):
        """
        Creates a Track object and adds it to this collection.
        """

        track = Track()

        # Run track handlers:

        for hand in self.in_hands[TRACK]:

            hand(self, track, self.num_tracks)

        self.append(Track())

    def start_playback(self, index: int = 0, time: int = None):
        """
        Gets all attached tracks ready for playback.
        """

        self.playing_tracks = self.data.copy()
        self.playing = True

        self.started = False

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

        if track is None:

            # Special event, return it:

            return first_event

        # Get our first event:

        event = track.get()

        # Handle the event:

        self._handle_event(event, 0, self.out_hands)

        # Return the event:

        return event

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

        if track is None:

            # Special event, return it:

            return first_event

        # Run the time_get method:

        event = await track.time_get()

        # Handle the event:

        self._handle_event(event, 0, self.out_hands)

        # Return the event:

        return event

    def _get_newest(self) -> BaseEvent:
        """
        Gets the newest event from the all tracks.

        We return the newest event and the track it came from.

        :return: Newest event
        :rtype: BaseEvent
        """

        # Get each event and compare the ticks:

        first_event = None
        ticks = None
        track = None

        if not self.started:

            # Return StartPattern():

            self.started = True

            return StartPattern(6, self.format, len(self), self._divisions), None

        if self.stopped:

            # We have stopped! Raise an exception:

            raise StopPlayback()

        for num, temp_track in enumerate(self.playing_tracks):

            event = temp_track.current()

            # print("Considering track: {}".format(num))
            # print("With event: {}".format(event))
            # print("With tick: {}".format(event.tick))
            # print("With out index: {}".format(temp_track.out_index))

            if ticks is None or event.tick <= ticks:

                # Event comes sooner, log it:

                # print("Got sooner event: {}".format(event))
                # print("Event ticks: {}".format(event.tick))
                # print("Current ticks: {}".format(ticks))

                first_event = event
                ticks = event.tick
                track = temp_track

        if len(self.playing_tracks) == 0:

            # No more tracks!

            # print("No more tracks! Done playing!")

            self.playing = False

            # Return StopPattern

            return StopPattern(), None

        if first_event.statusmsg == META and first_event.type == TRACK_END:

            # This track is over, remove it from playing:

            # print("Track over! Removing track : {}".format(self.playing_tracks.index(track)))

            self.playing_tracks.remove(track)

            # print("Playing length: {}".format(len(self.playing_tracks)))
            # print("Total length: {}".format(len(self)))

        # print("With out index: {}".format(track.out_index))
        # print("With event: {}".format(first_event))

        return first_event, track


class Track(BaseContainer):
    """
    A track of MIDI events.

    We offer some useful helper methods that make
    altering and adding MIDI events a relatively painless affair.

    We inherit the default python list,
    so we support all list operations.
    """

    def __init__(self, load_default_in: bool = True, load_default_out: bool = True):

        super().__init__(DEFAULT_TRACK_IN, DEFAULT_TRACK_OUT,
                         load_default_in=load_default_in, load_default_out=load_default_out)

        self.name = ''  # Name of the track
        self._tempo = 120  # Tempo in Beats Per Minute
        self.instrument = ''  # Name of the instrument for this track

        self.interval = 50 / 1000
        self.lookahead = 75 * 1000

        self.index = 0  # Index we are on
        self.start_time = 0  # Time we have started on, we use the ymidi timer for this
        self.last_time = 0  # Time of the last event
        self.timesig_num = 4  # Numerator of the time signature
        self.timesig_den = 4  # Denominator of the time signature
        # number of microseconds per beat
        self._mpb = bpm_to_mpb(self.tempo, denom=self.timesig_den)
        self.divisions = 48  # divisions of this track

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

    def start_playback(self, index: int = 0, time: int = None):
        """
        Prepares this container for playback.

        We set the index to zero and set the start time.
        This method can also be used to reset the playback to the start!
        You can also manually specify the index and time values to be set.

        After this function is called,
        users should start extracting values from the collection immediately!
        """

        # Set the index:

        self.out_index = index

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

    def current(self) -> BaseEvent:
        """
        Gets the current event in the track.

        This is determined by using the 'out_id' parameter.

        :return: Current event ready to leave the track
        :rtype: BaseEvent
        """

        return self[self.out_index]

    def get(self) -> BaseEvent:
        """
        Gets the next event from the container.

        We also send our events though the track handlers.

        :return: The next handler in the container
        :rtype: BaseEvent
        """

        # Get the event:

        event = self[self.out_index]

        # Run the event though the handlers:

        self._handle_event(event, self.out_index, self.out_hands)

        # Increment the index:

        self.out_index += 1

        # Finally, return the event:

        return event

    async def time_get(self) -> BaseEvent:
        """
        Gets an event from the track,
        but does not do so until it is time for the event to be returned.

        This method uses a special method of time keeping to ensure that playback is accurate.
        We utilize a lookahead method of time keeping,
        meaning that if the event time falls within the lookahead,
        then it is returned.
        This lookahead, and the wait interval,
        can be configured as you see fit.
        TODO: Big ticket item, configure a benchmark or profiling system
        that can determine the most optimal values for this.

        This method requires the 'start_playback()' method to be called,
        otherwise playback may not be accurate.

        :return: Event to be returned
        :rtype: BaseEvent
        """

        # Determine the wait time:

        event = self[self.out_index]

        time_done = self.last_time + de_to_ms(event.delta, self.divisions, self._mpb)

        while True:

            # Get current time:

            current_time = ytime() + self.lookahead

            # Check if we are good to return:

            if time_done < current_time:

                # We are done!

                break

            # Sleep for a given time:

            await asyncio.sleep(self.interval)

        # Set the last time:

        self.last_time = ytime()

        # Return the event:

        return self.get()
