import math

import numpy as np
import pandas as pd


def extract_formation(pozyx_dict: dict, id_list: list, device_id, output_path: str, session_name: str,
                      fov_thres: int, distance_thres: int, do_correction: bool):
    """
    This part of code is to extract the f_formation data from interpolated pozyx data
    The pozyx yaw data may need to be corrected since the code assumed the radian should increase in the direction of
     from x to y, but sometimes pozyx increase the value from y to x.

    :param pozyx_dict: the dict containing all the Dataframe of interploated pozyx data
    :param id_list: list of all the id appeared in the pozyx_dict
    :param device_id: current device id
    :param output_path: path for output
    :param session_name: session name
    :param fov_thres: threshold of fov (field-of-view)
    :param distance_thres: threshold of distance between different positions
    :param do_correction: do correction or not
    :return:
    """

    result_dict = {
        "session_name": [session_name for _ in pozyx_dict[device_id]["timestamp"]],
        "timestamp": list(pozyx_dict[device_id]["timestamp"]),
    }
    for an_id in id_list:
        if an_id == device_id:
            result_dict[an_id] = [-1 for _ in pozyx_dict[device_id]["timestamp"]]
        else:
            result_dict[an_id] = [0 for _ in pozyx_dict[device_id]["timestamp"]]
    current_device_df = pozyx_dict[device_id]
    result_df = pd.DataFrame(result_dict)

    for a_id in id_list:
        if a_id != device_id:
            for i, line in current_device_df.iterrows():
                timestamp = current_device_df.iloc[i]["timestamp"]
                if timestamp in pozyx_dict[a_id]["timestamp"].values:
                    iterring_df = pozyx_dict[a_id]
                    line = iterring_df.loc[iterring_df["timestamp"] == timestamp].iloc[0]

                    iter_device_pos = np.array([line["x"], line["y"]])
                    param_device_pos = np.array([current_device_df.iloc[i]["x"], current_device_df.iloc[i]["y"]])
                    if _get_within_view(param_device_pos, float(current_device_df.iloc[i]["yaw"]), iter_device_pos,
                                        float(line["yaw"]), fov_thres, distance_thres, do_correction):
                        result_df.loc[i, a_id] = 1

    result_df.to_csv(output_path)


###################################################################
# code below may not be useful if you only want to apply the code #
###################################################################

def _correction(radian: float):
    return 2 * math.pi - radian


def _get_within_view(p1: np.ndarray, p1_yaw: float, p2: np.ndarray, p2_yaw: float, fov: int,
                     distance_thres: int, do_correction: bool):
    distance = np.linalg.norm(p1 - p2)
    if distance > distance_thres:
        return False

    if do_correction:
        p1_yaw = _correction(p1_yaw)
        p2_yaw = _correction(p2_yaw)

    p1_yaw_vec = np.array([math.cos(p1_yaw), math.sin(p1_yaw)])
    p2_yaw_vec = np.array([math.cos(p2_yaw), math.sin(p2_yaw)])

    p1_to_p2_vec = p2 - p1
    p2_to_p1_vec = p1 - p2
    dot_product_p1_p2 = np.dot(p1_to_p2_vec / np.linalg.norm(p1_to_p2_vec), p1_yaw_vec / np.linalg.norm(p1_yaw_vec))
    dot_product_p2_p1 = np.dot(p2_to_p1_vec / np.linalg.norm(p2_to_p1_vec), p2_yaw_vec / np.linalg.norm(p2_yaw_vec))
    # math.degree can be used to change radius to angle
    angle_p1_to_p2 = math.degrees(np.arccos(dot_product_p1_p2))
    angle_p2_to_p1 = math.degrees(np.arccos(dot_product_p2_p1))
    # print()

    if angle_p1_to_p2 < fov / 2 and angle_p2_to_p1 < fov / 2:
        return True
    else:
        return False
