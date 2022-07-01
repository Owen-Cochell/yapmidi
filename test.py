"""
A set of components and tools to test yap-midi components.    
"""

import asyncio
import struct

from ymidi.decoder import ModularDecoder, MetaDecoder
from ymidi.events.voice import NoteEvent
from ymidi.events.system.system_exc import SystemExclusive
from ymidi.events.builtin import StopPattern, StartTrack
from ymidi.events.meta import MetaText

from ymidi.io.file import MIDIFile


def midi_stream():
    # Test MIDI stream decoding:

    """
    This example byte stream is super weird,
    and is actually not valid MIDI data!
    Still, it is good to be able to handle stream interrupts,
    incase some synths implement this feature.
    """

    stream = [0x90,60,0xF8,0xF0,1,2,0xF8,3,4,5,0xF7,64,60,0x80,30,0xF8,0x90,55,55,30,64,78,23,0xF8]

    stream = bytes(stream)
    
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
        value = decoder.seq_decode(decoder.to_bytes(bts))
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

    file = MIDIFile('church.mid')

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

#midi_stream()
asyncio.run(midi_file())
