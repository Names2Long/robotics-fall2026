"""Decode a short browser WAV in memory using the lab's English vocabulary."""
from io import BytesIO
from array import array
import wave

from handover import PHRASES


def make_decoder():
    from pocketsphinx import Decoder

    grammar = "#JSGF V1.0; grammar handover; public <command> = "
    grammar += " | ".join(PHRASES) + ";"
    decoder = Decoder(lm=None, samprate=16000, loglevel="ERROR")
    decoder.add_jsgf_string("handover", grammar)
    decoder.activate_search("handover")
    return decoder


def transcribe(decoder, recording):
    try:
        with wave.open(BytesIO(recording), "rb") as wav:
            if wav.getframerate() != 16000 or wav.getnchannels() != 1 or wav.getsampwidth() != 2:
                raise ValueError("Record mono 16 kHz audio using the guide's microphone.")
            if not 1600 <= wav.getnframes() <= 160000:
                raise ValueError("Record one short command between 0.1 and 10 seconds.")
            pcm = wav.readframes(wav.getnframes())
    except (wave.Error, EOFError) as error:
        raise ValueError("The recording could not be read. Try again.") from error
    samples = array("h")
    samples.frombytes(pcm)
    if not samples or max(map(abs, samples)) < 80:
        raise ValueError("The recording is silent. Check your microphone and try again.")
    decoder.start_utt()
    try:
        decoder.process_raw(pcm, no_search=False, full_utt=True)
    finally:
        decoder.end_utt()
    hypothesis = decoder.hyp()
    return hypothesis.hypstr if hypothesis else ""
