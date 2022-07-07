"""
This file contains IO Modules that can use yap-midi containers.

These can be useful for putting events directly into a container
for manipullation, or extracting these events from a container.
These IO modules also support playback,
meaning that these modules can return events in proper time.

Another purpose of these IO modules is that they can
organize incoming events from another IO module.
This allows for events to come in their proper order.
For example if we are working with the MIDIFile IO module,
then events may not come in order, because concurrent events
in other tracks are not parsed at the same time.
These IO modules will pull all events from the IO module
and work with them appropiately.
"""

from ymidi.io.base import BaseIO


class ContainerIO(BaseIO):
    """
    ContainerIO - Uses yap-midi containers to work with events.

    This IO module will input events into a yap-midi container,
    and extract events from the same yap-midi container.
    It's kinda like EchoIO in the sense that you get what you put in,
    but this module has a few extra features that EchoIO lacks.

    This IO module can pull events from any IO module,
    which means that any events that are extrcated from the source IO module
    will be stored and sorted into the collection we are bound to.
    This also means that any processing or sorting that the container
    is configured to do will be in effect.

    We also support proper playback of events in our container,
    which means that events can be outputted in a muscily valid way.
    For example, if an event has a delay(delta time) before it is to be played,
    then this IO module will wait to output it until it is ready.

    One useful application of this IO module is to return 
    events from MIDI files in the order they are encountered.
    The MIDIFile IO module returns events in the order they are encountred.
    This means that any events in other tracks will not be returned
    until the current track is complete.
    Because these tracks are concurrent, you will not
    recieve events in the order they were meant to be encountered.
    This IO module will sort these events(if the container has this functionality enabled),
    and return them in the proper order.
    """