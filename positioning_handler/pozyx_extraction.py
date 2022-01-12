"""
Extracting pozyx data
"""

import json
import math

import numpy as np
import pandas
from scipy import interpolate


# This function is about getting the
def generate_single_file(output_path: str, pozyx_dict: dict, device_id, session_name: str):
    """
    the function that would be call.
    It uses raw pozyx file to generate the positioning data for all the four students.
    The output files only contain the positioning data for every second.
    """

    # extract pozyx data
    # a_dict = generate_poxyz_data_R(raw_pozyx_path)
    interpolation_result = _get_interpolated_data(pozyx_dict[device_id])
    interpolation_result["session_name"] = session_name
    interpolation_result.to_csv(output_path)


def generate_poxyz_data_R(path: str, device_ids: list):
    a_dict = {}

    for device_id in device_ids:
        a_dict[device_id] = _gen_sub_dict()

    jsons = _loading_json(path)
    for line in jsons:
        tag_id = int(line["tagId"])
        if tag_id in device_ids:
            if bool(line["success"]):
                a_dict[tag_id]["timestamp"].append(line["timestamp"])
                a_dict[tag_id]["success"].append(line["success"])
                a_dict[tag_id]["x"].append(line["data"]["coordinates"]["x"])
                a_dict[tag_id]["y"].append(line["data"]["coordinates"]["y"])
                a_dict[tag_id]["yaw"].append(line["data"]["orientation"]["yaw"])

    return a_dict

###################################################################
# code below may not be useful if you only want to apply the code #
###################################################################

def _gen_sub_dict():
    another_dict = {}
    another_dict["timestamp"] = []
    another_dict["success"] = []
    another_dict["x"] = []
    another_dict["y"] = []
    another_dict["yaw"] = []
    return another_dict


def _loading_json(path: str):
    json_list = []
    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:

            # this len > 3 is to prevent the lines only contain a \n or something else
            if len(line) > 3:
                string = line.strip()
                json_list.append(json.loads(string[1:-1]))
    return json_list


def _get_interpolated_data(data_frame):
    """
    using scipy to generate a interpolation model for the data points
    :param data_frame: data frame for a student
    :return: an scipy interpolation model
    """

    timestamp_array = np.array(data_frame["timestamp"])
    # timestamp = original_timestamp
    pozyx_x = np.array(data_frame["x"])
    pozyx_y = np.array(data_frame["y"])
    pozyx_yaw = np.array(data_frame["yaw"])

    interpolate_x = interpolate.interp1d(timestamp_array, pozyx_x, kind="linear")
    interpolate_y = interpolate.interp1d(timestamp_array, pozyx_y, kind="linear")
    interpolate_yaw = interpolate.interp1d(timestamp_array, pozyx_yaw, kind="linear")

    timestamp_ints = np.array(range(math.ceil(min(timestamp_array)), int(max(timestamp_array)) + 1))

    interpolated_dataframe = pandas.DataFrame({
        "timestamp": timestamp_ints,
        "x": interpolate_x(timestamp_ints),
        "y": interpolate_y(timestamp_ints),
        "yaw": interpolate_yaw(timestamp_ints)
    })
    return interpolated_dataframe
