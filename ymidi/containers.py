"""
Components that house MIDI events and other misc. data, 
"""

from dataclasses import dataclass


class TrackInfo(dataclass):
    """
    An object that contains info about a specific track.
    
    The data in this object is used for keeping track of track statistics.
    We allow for these attributes to be manually defined,
    and we also allow for auto-track traversal to fill in this info.
    """

    pass

class TrackPattern(list):
    """
    A collection of tracks.
    
    We contain a list of tracks that contain MIDI events.
    We keep track(haha) of statistics and data related to the
    MIDI data we contain.
    We do this by handling Meta events and yap-events.
    
    We also support playback of the MIDI data.
    This includes ALL MIDI track types,
    and supports tracks that are playing at diffrent speeds.
    """
    
    pass


class Track(list):
    """
    A track of MIDI events.
    
    We offer some useful helper methods that make
    altering and adding MIDI events a relatively painless affair.

    We inherit the default python list,
    so we support all list operations.
    """

    def __init__(self, *args):
        
        super().__init__(*args)

        self.name = ''  # Name of the track
