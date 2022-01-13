# Feature extraction example

This folder holds an example of how to do feature extraction. Users need to run the mission_preprocessing.json then run the mission_feature.json.

	python run_code.py examples/feature_extraction_example/mission_preprocessing.json
	python run_code.py examples/feature_extraction_example/mission_feature.json

## Folders

### discussion

Two wav files and their processed csv results of a scenario that two students discuss together.

### f_formation_data

The csv files of each person's formation information.

### feature_output

The feature extraction output csv files of each scenarios.

### group handover

Three wav files and their processed csv results of a scenario that one student gives a handover to another student, while the remaining one student is taking care of a patient.

### pozyx_output

The folder holding the processed pozyx data. 

### separate

Two wav files and their processed csv results of a scenario that two students work individually.

## Files

### mission_feature.json

mission json contains the missions of feature extraction. Users need to run it after running the preprocessing json. 

### mission_preprocessing.json

mission json contains the missions of preprocessing. It contains all the preprocessing procedures to generate the files required by feature extractions. 

### pozyx_data.json

raw pozyx data