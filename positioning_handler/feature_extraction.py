import logging
import math

import pandas as pd


def feature_extraction(audio_data_dict: dict, f_foramtion_data_dict: dict, id_list: list,
                       audio_start_timestamp: float, connected_threshold: float, merging_threshold: float,
                       feature_list: list, session_name: str, output_path: str):
    """
    :return:
    """
    # preprocessing the audio segments data
    result_dict = {"id": id_list, }
    segment_dict = {}
    for i in range(len(id_list)):
        a_segment_list = []

        for index, line in audio_data_dict[id_list[i]].iterrows():
            a_segment_list.append((line["voice_start"], line["voice_end"]))

        a_segment_list = _merging_small_segments(a_segment_list, merging_threshold)
        segment_dict[id_list[i]] = a_segment_list

    # start to extract data
    feature_dict = {}
    for a_feature in feature_list:
        if a_feature in ("overlapped", "connected", "to_other"):
            feature_dict[a_feature + "_count"] = []
            feature_dict[a_feature + "_duration"] = []
        elif a_feature == "speaking_time":
            feature_dict[a_feature + "_duration"] = []
        else:
            logging.warning("unexpected feature in given feature list for extraction, received '{}'".format(a_feature))

    for i, an_id in enumerate(id_list):
        target_segment_dict = _get_target_segment_dict(an_id, segment_dict)

        if "overlapped" in feature_list:
            olp_result = _get_overlap_data(segment_dict[an_id], an_id, audio_start_timestamp, target_segment_dict,
                                           f_foramtion_data_dict)
            feature_dict["overlapped_count"].append(olp_result[0])
            feature_dict["overlapped_duration"].append(olp_result[1])

        if "connected" in feature_list:
            con_result = _get_connect_data(segment_dict[an_id], an_id, audio_start_timestamp, target_segment_dict,
                                           f_foramtion_data_dict, connected_threshold)
            feature_dict["connected_count"].append(con_result[0])
            feature_dict["connected_duration"].append(con_result[1])

        if "speaking_time" in feature_list:
            spk_result = _get_speaking_time(segment_dict[an_id])
            feature_dict["speaking_time_duration"].append(spk_result)

        if "to_other" in feature_list:
            oth_result = _get_to_other_data(segment_dict[an_id], an_id, audio_start_timestamp, target_segment_dict,
                                            f_foramtion_data_dict, connected_threshold)
            feature_dict["to_other_count"].append(oth_result[0])
            feature_dict["to_other_duration"].append(oth_result[1])

    result_dict = {"device_id": id_list, "session_name": [session_name for _ in range(len(id_list))]}
    for a_key in feature_dict.keys():
        result_dict[a_key] = feature_dict[a_key]
    pd.DataFrame(result_dict).to_csv(output_path)


###################################################################
# code below may not be useful if you only want to apply the code #
###################################################################

def _merging_small_segments(segment_list: list, threshold: float):
    """
    merging the small voice segments that may from an utterance
    :param segment_list: a list of segments
    :param threshold: threshold to do the merge
    :return: a merged segment list
    """
    merged_list = []
    merging_buffer_pos = []
    for i in range(len(segment_list)):
        if len(merging_buffer_pos) == 0:
            merging_buffer_pos.append(segment_list[i][0])
            merging_buffer_pos.append(segment_list[i][1])
        else:
            if segment_list[i][0] - merging_buffer_pos[1] < threshold:
                merging_buffer_pos[1] = segment_list[i][1]
            else:
                merged_list.append(merging_buffer_pos)
                merging_buffer_pos = []
                merging_buffer_pos.append(segment_list[i][0])
                merging_buffer_pos.append(segment_list[i][1])

    if len(merging_buffer_pos) != 0:
        merged_list.append(merging_buffer_pos)

    return merged_list


def _get_connect_data(main_segment_list: list, main_id, audio_start_timestamp: float, target_segment_dict: dict,
                      f_formation_dict: dict, connected_thres: float = 1.5):
    """the function to extract connected data """
    connected_count = 0
    connected_duration = 0

    for a_segment in main_segment_list:
        a_result = _determine_connect_data(a_segment, target_segment_dict, main_id, audio_start_timestamp,
                                           f_formation_dict, connected_thres)
        connected_count += a_result[0]
        connected_duration += a_result[1]

    return connected_count, connected_duration


def _determine_who_in_formation_with_main(main_segment, main_id, audio_start_timestamp: float, f_formation_dict):
    """
    determine which participants are creating f_formation with the participant who made this utterance
    (expressed with main segment)
    """
    start_timestamp = math.floor(main_segment[0] + audio_start_timestamp)
    end_timestamp = math.ceil(main_segment[1] + audio_start_timestamp)
    target_timestamp_list = list(range(start_timestamp, end_timestamp + 1))
    formation_df = f_formation_dict[main_id]

    result_list = []
    for an_id in f_formation_dict.keys():
        if an_id != main_id:
            a_df = formation_df[["timestamp", str(an_id)]]
            has_formtion_count = 0

            for a_timestamp in target_timestamp_list:
                if a_timestamp in a_df["timestamp"].values:
                    if a_df.loc[a_df["timestamp"] == a_timestamp].iloc[0][str(an_id)] == 1:
                        has_formtion_count += 1

            if has_formtion_count >= len(target_timestamp_list) * 0.7:
                result_list.append(an_id)

    return result_list


def _determine_connect_data(main_segment, target_segment_dict: dict, main_id, audio_start_timestamp: float,
                            f_formation_dict: dict, connected_thres: float = 1.5):
    """the logic to detect connected speech"""
    is_connected = False
    connected_duration = 0
    connected_count = 0
    formation_target_list = _determine_who_in_formation_with_main(main_segment, main_id, audio_start_timestamp,
                                                                  f_formation_dict)

    # this list has nothing means the student is not forming formation but talking,
    # it cannot create any connected speech in this situation

    if len(formation_target_list) == 0:
        return 0, 0

    for an_target_id in target_segment_dict.keys():
        if an_target_id not in formation_target_list:
            continue
        for a_segment in target_segment_dict[an_target_id]:

            main0_tar0 = main_segment[0] - a_segment[0]
            main0_tar1 = main_segment[0] - a_segment[1]
            main1_tar0 = main_segment[1] - a_segment[0]
            main1_tar1 = main_segment[1] - a_segment[1]
            main_len = main_segment[1] - main_segment[0]
            tar_len = a_segment[1] - a_segment[0]

            if main0_tar0 <= 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 >= 0:
                is_connected = True

            elif main0_tar0 < 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 < 0:
                if main_len > tar_len:
                    is_connected = True

            elif main0_tar0 <= 0 and main0_tar1 <= 0 and main1_tar0 <= 0 and main1_tar1 <= 0:
                if a_segment[0] - main_segment[1] < connected_thres and main_len > tar_len:
                    is_connected = True

            if is_connected:
                connected_count += 1
                connected_duration += main_len

                return connected_count, connected_duration
    # if it fits no situation listed above, it is not a connected speech
    return 0, 0


def _get_target_segment_dict(main_id, segment_dict: dict):
    """get a segment list that contains a segment dict that does not contain the currently investigating id"""
    result_dict = {}
    for an_id in segment_dict.keys():
        if an_id != main_id:
            result_dict[an_id] = segment_dict[an_id]
    return result_dict


def _get_overlap_data(main_segment_list: list, main_id, audio_start_timestamp: float, target_segment_dict: dict,
                      f_formation_dict: dict):
    """the function to detect overlapped speech"""

    overlap_count = 0
    overlap_duration = 0

    for a_segment in main_segment_list:
        a_result = _determine_overlap_data(a_segment, target_segment_dict, main_id, audio_start_timestamp,
                                           f_formation_dict)
        overlap_count += a_result[0]
        overlap_duration += a_result[1]

    return overlap_count, overlap_duration


def _determine_overlap_data(main_segment, target_segment_dict: dict, main_id, audio_start_timestamp: float,
                            f_formation_dict: dict):
    """the logic to detect connected speech"""
    is_overlapped = False
    overlapped_duration = 0
    overlapped_count = 0
    formation_target_list = _determine_who_in_formation_with_main(main_segment, main_id, audio_start_timestamp,
                                                                  f_formation_dict)

    # this list has nothing means the student is not forming formation but talking,
    # it cannot create any connected speech in this situation

    if len(formation_target_list) == 0:
        return 0, 0

    overlapped_segment_list = []

    for an_target_id in target_segment_dict.keys():
        if an_target_id not in formation_target_list:
            continue

        for a_segment in target_segment_dict[an_target_id]:

            main0_tar0 = main_segment[0] - a_segment[0]
            main0_tar1 = main_segment[0] - a_segment[1]
            main1_tar0 = main_segment[1] - a_segment[0]
            main1_tar1 = main_segment[1] - a_segment[1]

            if main0_tar0 <= 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 >= 0:
                is_overlapped = True
                overlapped_segment_list.append((a_segment[0], a_segment[1]))

            elif main0_tar0 > 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 > 0:
                is_overlapped = True
                overlapped_segment_list.append((main_segment[0], a_segment[1]))

            elif main0_tar0 < 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 < 0:
                is_overlapped = True
                overlapped_segment_list.append((a_segment[0], main_segment[1]))

            elif main0_tar0 >= 0 and main0_tar1 <= 0 and main1_tar0 >= 0 and main1_tar1 <= 0:
                # tar region is larger, so does not consider as overlapped
                is_overlapped = True
                overlapped_segment_list.append((main_segment[0], main_segment[1]))
    # because one segment can have overlap with multiple other segments,
    if is_overlapped:
        overlapped_count += 1
        overlapped_duration += _get_overlapped_duration(overlapped_segment_list)
        return overlapped_count, overlapped_duration
    # if it fits no situation listed above, it is not a connected speech
    return 0, 0


def _merge_segments(list_to_merge: list):
    """merge the segment that has overlap to a list of segments that do not have overlap"""
    while True:
        to_break = False
        for i, a_segment in enumerate(list_to_merge):
            for j, other_segment in enumerate(list_to_merge):
                if a_segment is not other_segment:
                    if a_segment[0] <= other_segment[1] and a_segment[1] >= other_segment[0]:
                        list_to_merge.remove(a_segment)
                        list_to_merge.remove(other_segment)
                        list_to_merge.append((min(a_segment[0], other_segment[0]), max(a_segment[1], other_segment[1])))
                        to_break = True
                        break
            if to_break:
                break
        if not to_break:
            break
    return list_to_merge


def _get_overlapped_duration(overlapped_segment_list):
    """get the length of segments in a segment list"""
    new_list = _merge_segments(overlapped_segment_list)
    duration = 0
    for a_segment in new_list:
        duration += (a_segment[1] - a_segment[0])
    return duration


def _get_speaking_time(main_segment_list):
    """ calculating the speaking time"""
    duration = 0
    for a_segment in main_segment_list:
        duration += (a_segment[1] - a_segment[0])
    return duration


def _get_to_other_data(main_segment_list: list, main_id, audio_start_timestamp: float, target_segment_dict: dict,
                       f_formation_dict: dict, connected_thres: float = 1.5):
    """function to get the speech to other (to_other) feature """
    to_other_count = 0
    to_other_duration = 0

    for a_segment in main_segment_list:
        a_result = _determine_to_other_data(a_segment, target_segment_dict, main_id, audio_start_timestamp,
                                            f_formation_dict, connected_thres)
        to_other_count += a_result[0]
        to_other_duration += a_result[1]

    return to_other_count, to_other_duration


def _determine_to_other_data(main_segment, target_segment_dict: dict, main_id, audio_start_timestamp: float,
                             f_formation_dict: dict, connected_thres: float = 1.5):
    """logic of get the speech to other"""
    is_to_other = True
    formation_target_list = _determine_who_in_formation_with_main(main_segment, main_id, audio_start_timestamp,
                                                                  f_formation_dict)

    # this list has nothing means the student is not forming formation but talking,
    # it cannot create any connected speech in this situation

    if len(formation_target_list) == 0:
        return 1, (main_segment[1] - main_segment[0])

    for an_target_id in target_segment_dict.keys():
        if an_target_id not in formation_target_list:
            continue
        for a_segment in target_segment_dict[an_target_id]:

            main0_tar0 = main_segment[0] - a_segment[0]
            main0_tar1 = main_segment[0] - a_segment[1]
            main1_tar0 = main_segment[1] - a_segment[0]
            main1_tar1 = main_segment[1] - a_segment[1]

            # all of the conditions below may indicate that the student is talking to someone inside the team
            if main0_tar0 <= 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 >= 0:
                is_to_other = False
            elif main0_tar0 > 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 > 0:
                is_to_other = False

            elif main0_tar0 < 0 and main0_tar1 < 0 and main1_tar0 > 0 and main1_tar1 < 0:
                is_to_other = False

            elif main0_tar0 >= 0 and main0_tar1 <= 0 and main1_tar0 >= 0 and main1_tar1 <= 0:
                is_to_other = False

            elif main0_tar0 <= 0 and main0_tar1 <= 0 and main1_tar0 <= 0 and main1_tar1 <= 0 and \
                    a_segment[0] - main_segment[1] < connected_thres:
                is_to_other = False


            elif main0_tar0 >= 0 and main0_tar1 >= 0 and main1_tar0 >= 0 and main1_tar1 >= 0 and \
                    main_segment[0] - a_segment[1] < connected_thres:
                is_to_other = False

            if not is_to_other:
                return 0, 0
    # if it fits no situation listed above, it is not a connected speech
    return 1, (main_segment[1] - main_segment[0])
