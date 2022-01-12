"""
This code file is the one you should run in the console to
"""

import json
import sys
import logging

import pandas as pd

from positioning_handler.f_formation import extract_formation
from positioning_handler.feature_extraction import feature_extraction
from positioning_handler.pozyx_extraction import generate_poxyz_data_R
from positioning_handler.pozyx_extraction import generate_single_file
from webrtc_with_CMUSphinx.voice_activity_detection import vad_on_unlabelled_data, vad_on_unlabelled_data_segments


def _main(argv):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    error_mission_list = []

    with open(argv[0]) as f:
        mission_json = json.load(f)

    logging.info("json file loaded")
    logging.info("start to execute missions")
    for i, a_misson in enumerate(mission_json):

        logging.info("executing mission number {}".format(i))

        if a_misson["mission_type"] == "do_vad":
            logging.info("running voice activity detection system")
            _do_vad(a_misson)

        elif a_misson["mission_type"] == "f_formation":
            logging.info("extracting f-formation data")
            _get_f_formation(a_misson)

        elif a_misson["mission_type"] == "interpolate_pozyx":
            logging.info("extracting interpolated pozyx data")
            _interplolate_pozyx(a_misson)

        elif a_misson["mission_type"] == "feature_extraction":
            logging.info("doing feature extraction")
            _extract_features(a_misson)

        else:
            logging.warning("unexpected mission type, received '{}' in number {} mission (start from 0)".format(
                a_misson["mission_type"], i))
            error_mission_list.append((i, a_misson["mission_type"]))

    logging.info("all mission finished")
    for an_error in error_mission_list:
        logging.warning("mission number {} is not a supported mission, received '{}'".format(an_error[0], an_error[1]))


def _do_vad(mission_json):
    audio_path = str(mission_json["audio_path"])
    output_path = str(mission_json["output_path"])
    session_name = str(mission_json["session_name"])

    word_threshold = int(mission_json["word_thres"])
    number_of_thread = int(mission_json["thread_number"])

    time_type = str(mission_json["time_format"])

    if audio_path == "" or output_path == "" or session_name == "":
        print("audio_path and output_path and session_name must have input value")
        return

    # if time type has value, then use the export in seconds, if not,
    # generate the csv holding the start and end of each voiced segments
    if time_type == "hms" or time_type == "seconds":
        vad_on_unlabelled_data(audio_path=audio_path, output_path=output_path, session_name=session_name,
                               word_threshold=word_threshold, number_of_thread=number_of_thread,
                               time_type=time_type)
    # output csv using segments format is the only one can be used in feature extraction
    elif time_type == "segments":
        vad_on_unlabelled_data_segments(audio_path=audio_path, output_path=output_path, session_name=session_name,
                                        word_threshold=word_threshold, number_of_thread=number_of_thread)
    else:
        logging.warning("unsupported time_type, only 'segments', 'seconds', and 'hms' are expected")
    return


def _get_f_formation(mission_json):
    interpolated_pozyx_path = mission_json["interpolated_pozyx_path"]
    pozyx_device_id = mission_json["pozyx_device_id"]
    output_path = mission_json["output_path"]
    session_name = str(mission_json["session_name"])

    fov_thres = int(mission_json["fov_threshold"])
    distance_thres = int(mission_json["distance_threshold"])
    do_correction = bool(mission_json["correction"])
    data_dict = {}

    # fetch all the dat into a dict, then pass to the function
    for i in range(len(interpolated_pozyx_path)):
        data_dict[pozyx_device_id[i]] = pd.read_csv(interpolated_pozyx_path[i])

    for i in range(len(interpolated_pozyx_path)):
        extract_formation(data_dict, pozyx_device_id, pozyx_device_id[i], output_path[i], session_name,
                          fov_thres=fov_thres, distance_thres=distance_thres, do_correction=do_correction)


def _extract_features(mission_json):
    pozyx_device_id = mission_json["pozyx_device_id"]
    audio_data_path = mission_json["audio_data_path"]
    formation_path = mission_json["formation_path"]
    feature_list = mission_json["feature"]
    audio_start_timestamp = float(mission_json["audio_start_timestamp"])
    session_name = str(mission_json["session_name"])
    merging_threshold = float(mission_json["segment_merging_threshold"])
    connected_threshold = float(mission_json["connected_threshold"])
    output_path = str(mission_json["output_path"])
    # f-formation的文件就是talk to relation,
    audio_data_dict = {}
    formation_data_dict = {}

    for i, a_path in enumerate(audio_data_path):
        audio_data_dict[pozyx_device_id[i]] = pd.read_csv(a_path)
    for i, a_path in enumerate(formation_path):
        formation_data_dict[pozyx_device_id[i]] = pd.read_csv(a_path)

    feature_extraction(audio_data_dict, formation_data_dict, pozyx_device_id,
                       audio_start_timestamp, connected_threshold, merging_threshold, feature_list,
                       session_name, output_path)


def _interplolate_pozyx(mission_json):
    pozyx_path = str(mission_json["pozyx_path"])
    pozyx_device_ids = mission_json["pozyx_device_id"]
    output_path = mission_json["output_path"]
    session_name = str(mission_json["session_name"])

    # execution

    pozyx_dict = generate_poxyz_data_R(pozyx_path, pozyx_device_ids)

    for i in range(len(pozyx_device_ids)):
        generate_single_file(output_path[i], pozyx_dict, pozyx_device_ids[i], session_name)


if __name__ == '__main__':
    # print(sys.argv)
    _main(sys.argv[1:])
