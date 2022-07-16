"""
This file contains track handlers.

Track handlers are functions that alter the state of a track container.
These are great for altering the state of the collection based upon events coming in or out.
For example, as events leave the queue during playback,
these handlers will change the tempo when we encounter a SetTempo event.

While these aren't 'conventional' handlers in the sense that they are functions(not classes),
and lack state chain methods such as start(), stop(), ect. ,
they will still live under the 'handlers' directory.

Track handlers expect the container that is being altered, the event that is being added,
and the index where the event is being added.
This is useful if events are inserted or appended into positions.
If a track handler returns anything that does not evaluate to false,
then the handle operation will be stopped, and no other handlers will be called.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from ymidi.constants import TEMPO_SET

from ymidi.events.base import BaseEvent
from ymidi.events.builtin import StartPattern, StopPattern
from ymidi.events.meta import EndOfTrack, InstrumentName, SetTempo, TimeSignature, TrackName
from ymidi.misc import de_to_ms, ms_to_de, ytime

if TYPE_CHECKING:
    from ymidi.containers import Track, Pattern


def append_event(track: Track, event: BaseEvent, index: int):
    """
    Simply appends the event to the end of the given track.

    :param track: Track to work with
    :type track: Track
    :param event: Event to append
    :type event: BaseEvent
    :param index: Current index
    :type index: int
    """

    track.append(event)


def track_name(track: Track, event: TrackName, index: int):
    """
    Changes the 'name' attribute of the track to the value in the TrackName.

    :param track: Track to change
    :type track: BaseContainer
    :param event: TrackName event
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    track.name = event.text


def instrument_name(track: Track, event: InstrumentName, index: int):
    """
    Changes the 'instrument' attribute of the track to the value in InstrumentName.

    :param track: Track to change
    :type track: BaseContainer
    :param event: InstrumentName event
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    track.instrument = event.text


def set_tempo(track: Track, event: SetTempo, index: int):
    """
    Changes the 'tempo' attribute of the track to the value in InstrumentName.

    We also set the microseconds per beat to match the bpm

    :param track: Track to alter
    :type track: BaseContainer
    :param event: SetTempo event
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    track.msb = event.tempo


def time_signature(track: Track, event: TimeSignature, index: int):
    """
    Sets the time signature on the given track.

    :param track: Track to alter
    :type track: Track
    :param event: Time signature event
    :type event: TimeSignature
    :type event: BaseEvent
    :param index: Index of the event 
    :type index: int
    """

    track.timesig_den = event.denominator
    track.timesig_num = event.numerator


def global_tempo(track: Pattern, event: SetTempo, index: int):
    """
    Changes the tempo of all tracks attached to us.

    This should ONLY be bound to Patterns(something that holds tracks),
    and should only be used in type 1 files
    where the tempo of all tracks should be synchronized.

    :param track: Pattern to alter
    :type track: Pattern
    :param event: SetTempo event
    :type event: SetTempo
    :param index: Index of the event
    :type index: int
    """

    print("Applying global tempo...")

    for track in track:

        # Set the tempo on this track:

        track.mpb = event.tempo


def create_tracks(pattern: Pattern, event: StartPattern, index: int):
    """
    Automatically creates track objects in a pattern.

    We expect to be bound to the StartPattern event.

    :param track: Container object to work with
    :type track: Pattern
    :param event: Event to work with, ideally StartPattern
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    # Create each track and add it:

    print("Creating tracks...")

    for _ in range(event.num_tracks):

        pattern.add_track()


def attach_global_tempo(pattern: Pattern, event: StartPattern, index: int):
    """
    Determines if it is necessary to attach the 'global_tempo()' track handler.

    As of now, we only do this if the format is 1.

    :param pattern: Pattern to work with
    :type pattern: Pattern
    :param event: StartPattern event
    :type event: StartPattern
    :param index: Event index we are on
    :type index: int
    """

    # Attach the global tempo object:

    print("Attaching global_tempo...")

    input()

    if event.format == 1:

        pattern.out_hands[TEMPO_SET].append(global_tempo)


def start_pattern(pattern: Pattern, event: StartPattern, index: int):
    """
    Extracts info from the StartPattern event and applies it to the Pattern.

    We expect to be bound to a StartPattern event.

    :param pattern: Pattern to alter
    :type pattern: Pattern
    :param event: StartPattern event
    :type event: StartPattern
    :param index: Index of the event
    :type index: int
    """

    pattern.divisions = event.divisions
    pattern.format = event.format

    print("Format: {}".format(pattern.format))
    print("Divisions: {}".format(event.divisions))

    input()

    return True


def stop_pattern(pattern: Pattern, event: StopPattern, index: int):
    """
    We do nothing but return True,
    so the StopPattern() is not stored in any tracks.

    :param pattern: Pattern to work with
    :type pattern: Pattern
    :param event: StopPattern event
    :type event: StopPattern
    :param index: Index of the event
    :type index: int
    """

    return True


def sort_events(pattern: Pattern, event: BaseEvent, index: int):
    """
    Sorts the given events into tracks.

    We check if the event has a valid track that is apart of.
    Otherwise, we make an educated guess by using track_index,
    which will add it to the current track we are working with.

    :param pattern: Pattern of tracks
    :type pattern: Pattern
    :param event: Event to add
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    print("Sorting event: {}".format(event))

    if event.track > -1:

        # Add the event to the given track:

        pattern[event.track].submit_event(event)

    else:

        # Guess, add the event to the track we are working with

        pattern[pattern.track_index].submit_event(event)


def stop_track(pattern: Pattern, event: EndOfTrack, index: int):
    """
    Increments the track index of the pattern.

    We should ONLY do this once the track is complete,
    i.e we get a EndOfTrack event.

    We only increment the index if there are other 
    objects in our collection!

    :param pattern: Pattern to alter
    :type pattern: Pattern
    :param event: EndOfTrack event
    :type event: EndOfTrack
    :param index: Index of the event
    :type index: int
    """

    print("Stopping track!")

    print(pattern.track_index)
    print(len(pattern))

    input()

    if pattern.track_index + 1 < len(pattern):

        # Increment the index:

        pattern.track_index += 1


def event_tick(container: Track, event: BaseEvent, index: int):
    """
    Sets the 'tick' parameter of the event, which is the
    number of ticks that come before this object.

    We use the tick value of the previous event to determine this.

    :param container: Container to alter
    :type container: Track
    :param event: Any event
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    # Determine the tick number, add total ticks plus delta:

    offset = 0

    if index > 0:

        offset = container[index-1].tick

    event.tick = offset + event.delta


def event_time(container: Track, event: BaseEvent, index: int):
    """
    Determines the time in milliseconds that come before this event.

    :param container: Container to alter
    :type container: Track
    :param event: Any event
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    offset = 0

    if index > 0:

        offset = container[index - 1].time

    event.time = offset + de_to_ms(event.delta, container.divisions, container._mpb)


def event_delta_time(container: Track, event: BaseEvent, index: int):
    """
    Sets the delta time in microseconds of the event.

    :param container: Container to alter
    :type container: Track
    :param event: Any event
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    event.delta_time = de_to_ms(event.delta, container.divisions, container._mpb)


def determine_delta(container: Track, event: BaseEvent, index: int):
    """
    Determines the delta time of this event.

    We check all values(and if this operation is necessary),
    and sets the delta time.

    This is important, as all operations rely on delta time.

    :param container: Track to work with
    :type container: Track
    :param event: Event to work with
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    # Check if we need to determine the delta time:

    if event.delta != 0:

        # No computations necessary!

        return

    # Delta time needed, see if we have a delta in microseconds:

    if event.delta_time != 0:

        # We definitely have a valid delta time!

        event.delta = ms_to_de(event.delta_time, container.divisions, container.tempo)

        return

    # These tests are a bit harder to do, but is a good sanity check:

    tick_before = 0
    time_before = 0

    if len(container) > 0:

        # Set the before values:

        tick_before = container[-1].tick
        time_before = container[-1].time

    # Check if we have a valid tick value:

    if tick_before <= event.tick:

        # We have a valid absolute tick value:

        event.delta = event.tick - tick_before

        return

    # Check if we hve valid time value:

    if time_before <= event.time:

        # We have a valid absolute time value:

        event.delta = ms_to_de(event.time - time_before, container.track, container.tempo)

        return
    
    # Check if our time identifiers are valid:

    if event.time == 0 and event.tick == 0:

        # Valid time identifiers, delta should just be zero:

        return

    # Time is NOT valid, event is trying to be somewhere is should not be, do something!
    #TODO: Figure this out!


def set_division(container: Pattern, event: Track, index: int):
    """
    Sets the divisions on the given track.

    This handler is used to sync the divisions with all added tracks.

    :param container: Pattern wo work with
    :type container: Pattern
    :param event: Track to work with
    :type event: Track
    :param index: Index of the event
    :type index: int
    """

    event.divisions = container._divisions


def rehandle(container: Track, event: BaseEvent, index: int):
    """
    Sends all loaded events through the input event handlers again(if necessary).

    This operation can be useful for updating the time values
    of events if an event is inserted in between two events.
    This is because determining time values are dependent on the events that come before.
    We ONLY use in handlers for the rehandle operation,
    which is the default operation.

    We first determine if a rehandle operation is necessary.
    We determine if the index being added is NOT at the end of the container,
    and if the event being added is NOT already present in the container.

    :param container: Container to alter
    :type container: Track
    :param event: Event to process
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    # Determine if a rehandle is necessary:

    if index < len(container) and event not in container:

        # Do a rehandle operation:

        container.rehandle()


def time_profile(container: Track, event: BaseEvent, index: int):
    """
    Timestamp events as they leave the container.

    This is useful for debugging purposes,
    specifically for determining the time delay of events.
    This value is stored under 'exit_time'.
    We also attach a delta time, which is the current time minus
    the start time of the container.
    You can use this value to determine how long the event was in the 
    collection since the start of playback.
    This value is stored under 'exit_delta'.

    :param container: Container to alter
    :type container: Track
    :param event: Event to timestamp
    :type event: BaseEvent
    :param index: Index of the event
    :type index: int
    """

    current = ytime()

    event.exit_time = current
    event.exit_delta = current - container.start_time
