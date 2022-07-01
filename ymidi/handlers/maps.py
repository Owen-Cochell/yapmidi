"""
This file contains default handler maps to be used in loading.

These maps are kept in a separate file to prevent circular dependencies.    
"""

from ymidi.constants import TEMPO_SET, TRACK_NAME, INSTRUMENT
from ymidi.handlers.track import TrackName, InstrumentName, SetTempo

# yap-midi value used for global handlers

GLOBAL = 'global'

DEFAULT_TRACK_IN = {TRACK_NAME: [TrackName], INSTRUMENT: [InstrumentName]}
DEFAULT_TRACK_OUT = {TEMPO_SET: [SetTempo]}

DEFAULT_PATTERN_IN = {}
DEFAULT_PATTERN_OUT = {}
