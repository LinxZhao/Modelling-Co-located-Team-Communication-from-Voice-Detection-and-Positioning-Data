# Modelling-Co-located-Team-Communication-from-Voice-Detection-and-Positioning-Data

## Introduction

This repository holds the source code of paper:

	-placeholder for publication information


The code has been adapted to be used without diving into the code. Users can simply execute the runcode.py in command line with a json file to execute the functions. For example:

	python run_code.py examples/VAD_example/mission.json


## Functionalities

The functionalities can be divided into three parts:

1. Voice Activity Detection (VAD).
2. Positioning data processing.
3. Feature extraction.

### Voice activity detection

The VAD system here combines the webrtcvad system (https://github.com/wiseman/py-webrtcvad) with CMUSphinx offline speech to text system (using Python SpeechRecognition library, https://github.com/Uberi/speech_recognition) to make the system robust to background noise. However, the processing speed is very slow due to applying the speech to text technique.

The intuition for combining them is that the noise falsely recognized as human voice cannot have a speech recognition result. An audio file would be first processed by webrtcvad system to get the voiced segments. Then, the speech to text system would process those voiced segments to find the voice segments that does not have "enough" (determine by a threshold set by user) words in transcription. Those segments very likely only contain noise.

The input wav files for VAD system should have frequency at 8000, 16000, or 32000, and encoded in 16bit unsigned PCM.

To use this functionality, users need to install the PocketSphinx-Python following the instruction in the SpeechRecognition repository.

#### Json file structure

An example can be found in the example folder.

	 {
        "mission_type": "do_vad",
        "audio_path": "examples/VAD_example/test_audio_1.wav", 
        "output_path": "examples/VAD_example/example_output/segment_output_format.csv",
        "session_name": "test_1",
        "word_thres": 1, 
        "thread_number": 1,
        "time_format": "segments"    
    },

The json file should contain seven items:
1. mission_type: indicates the functionality.
2. audio_path: shows the path of the audio file to be processed.
3. output_path: the output path for result in csv format. 
4. session_name: just a name decided by user. 
5. word_thres: A transcription of a voiced segment should have greater number of words than word_thres to be determined as a voiced segment that containing human voice. Usually, 1 is the best. However, if users want to hold the single word sentence, like "yes", "no", "correct", it can be set as 0. 
6. thread_number: the number of threads to increase the speed of processing.
7. time_format: determine the formats about presenting "time" in csv. It can be "segments", "seconds", and "hms". Note, only segments format is supported in feature extraction.

### Positioning data processing

This functionality is to process raw pozyx data to get usable positioning data. This function applies linear interpolation since pozyx devices do not transmit data in a constant frequency.

Another functionality is detecting if two persons are within the view of each other (calling it formation here).

#### Json file structure of pozyx processing
An example in pozyx_example folder:

	{
        "mission_type": "interpolate_pozyx",
        "pozyx_path": "examples/pozyx_example/pozyx_data.json",
        "pozyx_device_id": [
            27261,
            27160,
            27226,
            27263
        ],
        "output_path": [
            "examples/pozyx_example/interpolated_27261.csv",
            "examples/pozyx_example/interpolated_27160.csv",
            "examples/pozyx_example/interpolated_27226.csv",
            "examples/pozyx_example/interpolated_27263.csv"  
        ],
        "session_name": "interpolation"
    }

1. mission_type: indicates the functionality.
2. pozyx_path: indicates the path of raw pozyx data file.
3. pozyx_device_id: id number of pozyx devices. Its sequence should be aligne with the output_path
4. output_path: the paths of output csv of each pozyx device. Its sequence should be aligned with the pozyx_device_id
5. session_name: a name.

#### Json file structure of detecting formation
An example in pozyx_example folder:

	{
        "mission_type": "f_formation",
        "pozyx_device_id": [
            27261,
            27160,
            27226,
            27263
        ],
        "interpolated_pozyx_path": [
            "examples/pozyx_example/interpolated_27261.csv",
            "examples/pozyx_example/interpolated_27160.csv",
            "examples/pozyx_example/interpolated_27226.csv",
            "examples/pozyx_example/interpolated_27263.csv"  
        ],
        "output_path": [
            "examples/pozyx_example/formation_27261.csv",
            "examples/pozyx_example/formation_27160.csv",
            "examples/pozyx_example/formation_27226.csv",
            "examples/pozyx_example/formation_27263.csv"
        ],
        "fov_threshold": 180,
        "distance_threshold": 2000,
        "session_name": "f-formation",
        "correction": 1
    }
1. mission_type: indicates the functionality.
3. pozyx_device_id: id number of pozyx devices. Its sequence should be aligne with the output_path and interpolated_pozyx_path.
4. interpolated_pozyx_path: indicates the path of processed pozyx data file.
4. output_path: the paths of output csv of each pozyx device. 
5. fov_threshold: fov of a person for determining if other person is within the view.
6. distance_threshold: distance between two person should be less than this threshold to be determined as within view.
5. session_name: name.
6. correction: The pozyx yaw data may need to be corrected since the code assumed the radian should increase in the direction from x to y, but sometimes pozyx increase the value from y to x. Set correction to 1 if it increases from y to x.

### Feature extraction

This functionality is about non-verbal feature extraction introduced in the paper. It has four features: total speaking time, overlapped speech, connected speech, and speech to other. Each one is presented by count and duration.

#### Json file structure

An example in the feature_extraction_example folder

	{
        "mission_type": "feature_extraction",
        "pozyx_device_id": [
            27261,
            27226
        ],
        "audio_data_path": [
            "examples/feature_extraction_example/separate/separate_27261.csv",
            "examples/feature_extraction_example/separate/separate_27226.csv"

        ],
        "formation_path": [
            "examples/feature_extraction_example/f_formation_data/formation_27261.csv",
            "examples/feature_extraction_example/f_formation_data/formation_27226.csv"
        ],
        "feature":[
            "speaking_time",
            "overlapped",
            "connected",
            "to_other"
        ],
        "output_path": "examples/feature_extraction_example/feature_output/separate.csv",
        "audio_start_timestamp": 1630387900.504,
        "segment_merging_threshold": 1.5,
        "connected_threshold": 3,
        "session_name": "feature_extraction_separate"
    }

1. mission_type: indicates the functionality.
3. pozyx_device_id: id number of pozyx devices. Its sequence should be aligne with the audio_data_path and formation_path.
4. audio_data_path: the csv output of VAD of corresponding person, it should also align with formation_path, and pozyx_device_id
5. formation_path: the csv output of formation detection, it should also align with pozyx_device_id, and audio_data_path.
6. feature: features that would be included in the output csv
7. output_path: path for the output csv.
8. audio_start_timestamp: the unix timestamp of the start of corresponding audio data.
9. segment_merging_threshold: if two voiced segments are close enough, they would be merged into one. This threshold detemines what is close enough.
10. connected_threshold: the threshold used to determine how close between two segments should be considered as connected.
11. session_name: just a name.