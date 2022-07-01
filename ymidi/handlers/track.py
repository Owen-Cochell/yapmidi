"""
This file contains track handlers.

Track handlers are functions that alter the state of a track container.
These are great for altering the state of the collection based upon events coming in or out.
For example, as events leave the queue during playback,
these handlers will change the tempo when we encounter a SetTempo event.

While these aren't 'conventional' handlers in the sense that they are functions(not classes),
and lack state chain methods such as start(), stop(), ect. ,
they will still live under the 'handlers' directory.
"""

from ymidi.events.base import BaseEvent
from ymidi.events.builtin import StartPattern
from ymidi.events.meta import EndOfTrack
from ymidi.misc import bpm_to_mpb
from ymidi.containers import Track, Pattern


def TrackName(track: Track, event: BaseEvent):
    """
    Changes the 'name' attribute of the track to the value in the TrackName.

    :param track: Track to change
    :type track: BaseContainer
    :param event: TrackName event
    :type event: BaseEvent
    """

    track.name = event.text


def InstrumentName(track: Track, event: BaseEvent):
    """
    Changes the 'instrument' attribute of the track to the value in InstrumentName.

    :param track: Track to change
    :type track: BaseContainer
    :param event: InstrumentName event
    :type event: BaseEvent
    """

    track.instrument = event.text


def SetTempo(track: Track, event: BaseEvent):
    """
    Changes the 'tempo' attribute of the track to the value in InstrumentName.

    We also set the microseconds per beat to match the bpm

    :param track: Track to alter
    :type track: BaseContainer
    :param event: SetTempo event
    :type event: BaseEvent
    """

    track.tempo = event.tempo
    track.msb = bpm_to_mpb(track.temp, track.timesig_den)


def start_pattern(pattern: Pattern, event: StartPattern):
    """
    Extracts info from the StartPattern event and applies it to the Pattern.

    :param pattern: Pattern to alter
    :type pattern: Pattern
    :param event: StartPattern event
    :type event: StartPattern
    """
    
    pattern.msb = event.divisions


def create_tracks(pattern: Pattern, event: StartPattern):
    """
    Automatically creates track objects in a pattern.

    We expect to be bound to the StartPattern event.

    :param track: Container object to work with
    :type track: Pattern
    :param event: Event to work with, ideally StartPattern
    :type event: BaseEvent
    """

    # Create each track and add it:

    for num in range(event.num_tracks):

        pattern.append(Track())


def sort_events(pattern: Pattern, event: BaseEvent):
    """
    Sorts the given events into tracks.

    We use the track_index value in the Pattern
    to determine which track to add events to.

    :param pattern: Pattern of tracks
    :type pattern: Pattern
    :param event: Event to add
    :type event: BaseEvent
    """

    # Add the event to the given track:

    pattern[pattern.track_index].append(event)


def stop_track(pattern: Pattern, event: EndOfTrack):
    """
    Increments the track index of the pattern.
    
    We should ONLY do this once the track is complete,
    i.e we get a EndOfTrack event.

    :param pattern: Pattern to alter
    :type pattern: Pattern
    :param event: EndOfTrack event
    :type event: EndOfTrack
    """
    
    pattern.track_index += 1
