# Modelling-Co-located-Team-Communication-from-Voice-Detection-and-Positioning-Data

## Introduction

This repository holds the source code of paper:

	-placeholder for publication information


The code has been adapted to be used without diving into the code. Users can simply execute the runcode.py in command line with a json file to execute the functions. For example:

	

## Functionalities

The functionalities can be divided into three parts:

1. Voice Activity Detection (VAD).
2. Positioning data processing.
3. Feature extraction.

### Voice activity detection

The VAD system here combines the webrtcvad system (https://github.com/wiseman/py-webrtcvad) with CMUSphinx offline speech to text system (using Python SpeechRecognition library, https://github.com/Uberi/speech_recognition) to make the system robust to background noise.

To use this functionality, you need to install the PocketSphinx-Python following the instruction in the SpeechRecognition repository.


