"""
A set of components and tools to test yap-midi components.    
"""

import asyncio
import struct

from ymidi.decoder import ModularDecoder, MetaDecoder
from ymidi.events.voice import NoteEvent, NoteOff, NoteOn
from ymidi.events.system.system_exc import SystemExclusive
from ymidi.events.builtin import StopPattern, StartTrack
from ymidi.events.meta import MetaText
from ymidi.handlers.maps import GLOBAL
from ymidi.handlers.track import time_profile
from ymidi.io import container
from ymidi.io.file import MIDIFile
from ymidi.containers import Track, Pattern
from ymidi.io.base import RouteIO
from ymidi.io.container import ContainerIO
from ymidi.misc import ytime


def midi_stream():
    # Test MIDI stream decoding:

    """
    This example byte stream is super weird,
    and is actually not valid MIDI data!
    Still, it is good to be able to handle stream interrupts,
    incase some synths implement this feature.
    """

    stream = [0x90,60,0xF8,0xF0,1,2,0xF8,3,4,5,0xF7,64,60,0x80,30,0xF8,0x90,55,55,30,64,78,23,0xF8]

    #stream = bytes(stream)

    print(stream)
    print(type(stream))

    # Time, Time, SystemExclusive(1,2,3,4,5), On(60,64), Time, On(55,55), Off(30,30), On(60,64), On(78,23), Time 
    decoder = ModularDecoder()
    decoder.load_default()
    final = []

    #print(decoder.collection)

    # Decode the data:

    for bts in stream:

        print("Decoding value: {}".format(bts))
        print(type(bts))
        value = decoder.seq_decode(bts)
        print("Response: {}".format(value))

        if value is not None:

            final.append(value)
            
            if isinstance(value, NoteEvent):
                
                print("Pitch: {} ; Velocity: {}".format(value.pitch, value.velocity))

            if isinstance(value, SystemExclusive):
                
                print("SystemExc values: {}".format(value.data))

    print(final)


def variable_decode():
    
    # Test variable length decoding:
    
    stream = [0xF0, 1, 2, 3, 4, 5, 0xF7]
    
    decoder = ModularDecoder()
    decoder.load_default()
    final = []
    
    for bts in stream:
        
        print("Decoding value: {}".format(bts))
        value = decoder.seq_decode(bts)
        print("Response: {}".format(value))
        
        if value is not None:
            
            final.append(value)
            
        if isinstance(value, SystemExclusive):
            
            print("Data: {}".format(value.data))


def varlen_decoding():
    """
    Tests if we can decode variable length integers.
    """
    
    meta = MetaDecoder()
    
    # 59:
    
    byts = meta.write_varlen(0x0fffffff)
    
    print("Varlen: {}".format(byts))
    
    final = meta.read_varlen(byts)
    
    print("Final: {}".format(final))


async def midi_file():
    """
    Tests the MIDI file functionality.

    We load a MIDI file and inspect it's content.

    Test MIDI File Size: 2079 Bytes
    """

    # Create a MIDI File:

    file = MIDIFile('purcell_queen.mid')

    # Start the MIDI File:

    await file.start()

    start = await file.get()

    # Print some stats:

    print("Number of Tracks: {}".format(start.num_tracks))
    print("File format: {}".format(start.format))
    print("File length: {}".format(start.length))
    print("Divisions: {}".format(start.divisions))
    print("Builtin length: {}".format(len(start)))

    print(file.collection.qsize())

    while file.has_events():

        # Get the event:

        print("Getting event ...")

        event = await file.get()

        print(event)

        if isinstance(event, StartTrack):
            
            print("Start of track: {}".format(event.length))

        if event is StopPattern:
            
            print("End of MIDI file!")

            break

        if isinstance(event, MetaText):

            print("Text event, contents: {}".format(event.text))
            print(bytes(event))

    print("No more events!")


async def single_track():
    """
    Tests the single track functionality of yap-midi Track objects.
    """

    track = Track()

    # Add time_profile for performance testing:

    track.out_hands[GLOBAL].append(time_profile)

    on = NoteOn(1, 1)

    track.append(on)

    off = NoteOff(1,1)
    off.delta = 100

    track.append(off)

    on = NoteOn(2,2)
    on.delta = 200

    track.append(on)

    text = MetaText.fromstring("This is a test!")
    text.delta = 400

    track.append(text)

    off = NoteOff(4,4)
    off.delta = 300

    # This time, insert the object in between the on and text events:

    track.insert(3, off)

    # Print for fun:

    print(track)

    # Iterate and get some info:

    for event in track:

        print("Event: {}".format(event))
        print("Delta: {}".format(event.delta))
        print("Delta time: {}".format(event.delta_time))
        print("Tick number: {}".format(event.tick))
        print("Total time: {}".format(event.time))

    # Play the events:

    print("--------- Start Playback: ---------")

    track.start_playback()

    av = 0

    while track.index < len(track):

        res = await track.time_get()

        print("Got event: {}".format(res))
        print("Exit delta: {}".format(res.exit_delta))
        print("Actual time: {}".format(res.time))
        print("Time diff: {}".format(res.exit_delta - res.time))
        print("Time diff(seconds): {}".format((res.exit_delta - res.time) / 1000000))

        av += (res.exit_delta - res.time)

    print("--------- Stop Playback: ---------")

    av = av / len(track)

    print("Average time diff: {}".format(av))
    print("Average time diff (Seconds): {}".format(av / 1000000))


async def test_route():
    # Tests the IO routing capabilities of yap-midi

    loop = asyncio.get_running_loop()

    print(loop.is_running)

    pattern = ContainerIO()
    file = MIDIFile(path='majicalljarr.mid')
    route = RouteIO()

    # Connect the modules together:

    print("loading file...")

    route.load_input(file)

    print("Done loading file...")

    print("Loading pattern...")

    route.load_output(pattern)

    print("Done loading pattern....")

    # Wait until we are done:

    print("Waiting ...")

    #await route.tasks[0]

    #await asyncio.sleep(2)
    await file.wait()

    print("Done waiting!")

    # Output contents:

    for num, track in enumerate(pattern.container):

        print("------ Track: {} ------".format(num))

        print(track)

        print("------ End of Track: {} -------".format(num))
        print(track[-1].time)
        print(track[-1].time / 1000)
        print(track[-1].tick)
        print(track[-1].track)

    input()

    # Play the track!

    start = ytime()

    pattern.container.start_playback()

    print("Start playback!")

    while pattern.container.playing:

        # Get the event and output it:

        event = await pattern.container.time_get()

        print("Got event playing: {}".format(event))

    elapsed = ytime() - start

    print("Elapsed: {}".format(elapsed))
    print("Elapsed (Seconds): {}".format(elapsed / 1000000))

#midi_stream()
asyncio.run(test_route(), debug=True)
