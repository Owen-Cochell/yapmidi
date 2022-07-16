"""
This file contains default handler maps to be used in loading.

These maps are kept in a separate file to prevent circular dependencies.    
"""

from ymidi.constants import START_PATTERN, STOP_PATTERN, TEMPO_SET, TRACK_END, TRACK_NAME, INSTRUMENT
from ymidi.handlers.track import append_event, attach_global_tempo, create_tracks, event_delta_time, event_tick, event_time, rehandle, set_division, sort_events, start_pattern, stop_pattern, stop_track, track_name, instrument_name, set_tempo

# yap-midi value used for global handlers

GLOBAL = 'GLOBAL'

# Constant for identifying track objects:

TRACK = "TRACK"

# Track maps:

DEFAULT_TRACK_IN = {TRACK_NAME: [track_name],
    INSTRUMENT: [instrument_name],
    GLOBAL: [rehandle, event_tick, event_delta_time, event_time, append_event]}
DEFAULT_TRACK_OUT = {TEMPO_SET: [set_tempo]}

DEFAULT_PATTERN_IN = {
    START_PATTERN: [create_tracks, attach_global_tempo, start_pattern],
    STOP_PATTERN: [stop_pattern],
    TRACK_END: [sort_events, stop_track],
    TRACK: [set_division],
    GLOBAL: [sort_events]}
DEFAULT_PATTERN_OUT = {}
