import datetime

import pandas as pd
import pydub

from webrtc_with_CMUSphinx import webRTC_with_speech2text


def vad_on_unlabelled_data(audio_path: str, output_path: str, session_name: str, strictness_level: int = 3,
                           word_threshold: int = 1, number_of_thread: int = 0, time_type: str = "timestamp"):
    """
    This function is doing the VAD on unlabelled audio data.
    It will generate a new csv file containing the "session", "audio time", "audio" columns
    example can be found in VAD_example folder

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    ! DO remember that the audio file should be wav file, with frequency of 8000, 16000, or 32000 Hz
    ! And encoding with signed 16 bit PCM
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    :param audio_path: The path to audio file for VAD
    :param output_path: output path of the result csv
    :param session_name:
    :param strictness_level: the strictness level of WebRTC VAD, it should be 1, 2, or 3. Left it 3 is fine
    :param word_threshold: this threshold for setting how many words should a transcription of
     a voice segment contains to pass the check. It is set due to some background voice sometimes can be transcribed
      to one or two words. This threshold is to throw away this type of false positive.
      Increasing this value may lead to the increasing of recall and decreasing of precision.
    :param number_of_thread: number of thread for accelerate the computing time. 1 for not using multi-threading
    :param time_type: the format of time in the time column
    :return: the result DataFrame
    """
    # the result dataframe contains three columns called
    # "session", "audio time", "audio", containing the session name,
    # timestamp in the audio(in %H:%M:%S format), or in seconds
    # and the if the teacher spoke something(1 for teacher spoke something, 0 for not)
    a_df = _create_result_dataframe(audio_path, session_name, time_type)
    result_string = webRTC_with_speech2text.do_vad_with_speech_to_text(audio_path,
                                                                       strictness_level=strictness_level,
                                                                       word_threshold=word_threshold,
                                                                       number_of_thread=number_of_thread)

    if not len(result_string) == 0:
        # decode the return of the result
        for a_segment in result_string.split("|"):
            splitted = a_segment.split(",")
            start = float(splitted[0])
            end = float(splitted[1])

            time_array = _get_voiced_time(start, end, time_type)
            for a_time in time_array:
                the_line = a_df[a_df["audio time"] == a_time]

                # find the line that should be set to 1
                if len(the_line) != 0:
                    row = the_line.index.values.astype(int)[0]
                    a_df.iloc[row, a_df.columns.get_loc("audio")] = 1

    a_df.to_csv(output_path)
    return a_df


def vad_on_unlabelled_data_segments(audio_path: str, output_path: str, session_name: str, strictness_level: int = 3,
                                    word_threshold: int = 1, number_of_thread: int = 0):
    """
    almost the same with the upper one, with only some codes to create data in segment format, like (0.2, 1.2)
    csv contains columns ["session,	voice_start, voice_end"]
    example can be found in VAD_example folder
    """
    session = []
    voice_start = []
    voice_end = []

    result_string = webRTC_with_speech2text.do_vad_with_speech_to_text(audio_path,
                                                                       strictness_level=strictness_level,
                                                                       word_threshold=word_threshold,
                                                                       number_of_thread=number_of_thread)
    if not len(result_string) == 0:
        # decode the return of the result
        for a_segment in result_string.split("|"):
            splitted = a_segment.split(",")
            start = float(splitted[0])
            end = float(splitted[1])
            session.append(session_name)
            voice_start.append(start)
            voice_end.append(end)
    a_df = pd.DataFrame({"session": session, "voice_start": voice_start, "voice_end": voice_end})
    a_df.to_csv(output_path)


###################################################################
# code below may not be useful if you only want to apply the code #
###################################################################

def _get_voiced_time(start: float, end: float, result_type: str):
    """
    here are three types of methods mapping the time segment, like (1.22, 3.22),
    to specific timestamp (in per seconds way) in format of seconds or hour:minutes:seconds in "audio time" column

    :param start: start time of a segment, which is the first float in a segment
    :param end: end time of a segment
    :param result_type: depends on the time format in the json file.
    :return: a list containing the time string that should be marked as 1, in the same format in the data.csv.
    """

    # a_range = range(int(start), ceil(end) + 1)
    # a_range = range(ceil(start), round(end) + 1)
    a_range = range(round(start), round(end) + 1)

    an_array = []
    if result_type == "timestamp" or result_type == "hms":
        for a_time in a_range:
            an_array.append(str(datetime.timedelta(seconds=a_time)))
    elif result_type == "seconds":
        for a_time in a_range:
            an_array.append(str(a_time))
    else:
        raise Exception("Invalid value")
    return an_array


def _create_result_dataframe(audio_path: str, session_name: str, time_type: str):
    time_list = []
    audio = pydub.AudioSegment.from_wav(audio_path)
    # print(audio.duration_seconds)
    if time_type == "timestamp" or time_type == "hms":
        for i in range(int(audio.duration_seconds) + 1):
            time_list.append(str(datetime.timedelta(seconds=i)))
    elif time_type == "seconds":
        for i in range(int(audio.duration_seconds) + 1):
            time_list.append(str(i))
    a_df = pd.DataFrame({"audio time": time_list})
    a_df["session"] = session_name
    a_df["audio"] = 0
    a_df = a_df[["session", "audio time", "audio"]]

    return a_df
