"""
This file contains default handler maps to be used in loading.

These maps are kept in a separate file to prevent circular dependencies.    
"""

from ymidi.constants import START_PATTERN, TEMPO_SET, TRACK_END, TRACK_NAME, INSTRUMENT
from ymidi.handlers.track import create_tracks, event_delta_time, event_tick, event_time, rehandle, set_division, sort_events, start_pattern, stop_track, track_name, instrument_name, set_tempo

# yap-midi value used for global handlers

GLOBAL = 'GLOBAL'

# Constant for identifying track objects:

TRACK = "TRACK"

DEFAULT_TRACK_IN = {TRACK_NAME: [track_name],
    INSTRUMENT: [instrument_name],
    GLOBAL: [rehandle, event_tick, event_delta_time, event_time]}
DEFAULT_TRACK_OUT = {TEMPO_SET: [set_tempo]}

DEFAULT_PATTERN_IN = {
    START_PATTERN: [create_tracks, start_pattern],
    TRACK_END: [stop_track],
    TRACK: [set_division],
    GLOBAL: [sort_events]}
DEFAULT_PATTERN_OUT = {}
