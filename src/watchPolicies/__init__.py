from googleapiclient import errors
from .SplitBetweenWatchLaterAndLongWatchLater import SplitBetweenWatchLaterAndLongWatchLater
from .SaveAllToWatchLater import SaveAllToWatchLater
from .SaveAllToWatchNow import SaveAllToWatchNow
from .WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour import WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour


ONE_HOUR_IN_SECONDS = 60 * 60
THRITY_MINUTES_IN_SECONDS = 60 * 30

_watch_policies = []
for x in [
    {"require_min_duration": True, "postfix": ""},
    {"require_min_duration": False, "postfix": "IgnoreMinimum"}
]:
    _watch_policies.append(SplitBetweenWatchLaterAndLongWatchLater(divide_point=ONE_HOUR_IN_SECONDS, name="WatchPolicySaveLessThanHourToWatchLater" + x["postfix"], require_min_duration=x["require_min_duration"]))
    _watch_policies.append(SplitBetweenWatchLaterAndLongWatchLater(divide_point=THRITY_MINUTES_IN_SECONDS, name="WatchPolicySaveLessThan30MinutesToWatchLater" + x["postfix"], require_min_duration=x["require_min_duration"]))
    _watch_policies.append(SaveAllToWatchLater(name="SaveAllToWatchLater" + x["postfix"], require_min_duration=x["require_min_duration"]))
    _watch_policies.append(SaveAllToWatchNow(name="SaveAllToWatchNow" + x["postfix"], require_min_duration=x["require_min_duration"]))
    _watch_policies.append(WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour(name="WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour" + x["postfix"], require_min_duration=x["require_min_duration"]))

default_watch_policy="WatchPolicySaveLessThanHourToWatchLater"

def get_watch_policy(name):
    for x in _watch_policies:
        if x.name==name:
            return x
    raise Exception("Error invalid watch policy")

def get_policy_initial_context():
    return {
        "watch_later": [],
        "long_watch_later": [],
        "watch_now": []
    }

def _add_all_vids_to_playlist(loaded_output_playlists, list_of_videos, settings, youtube_helper):
    if len(list_of_videos)==0:
        return 0

    num_added = 0
    for vid in list_of_videos:
        try:
            num_added += loaded_output_playlists[settings["id"]].insert_video(video_id=vid["id"])
        except errors.HttpError as err:
            raise err

    return num_added

def sort_policy_context(policy_context):
    for key in policy_context.keys():
        policy_context[key] = sorted(policy_context[key], key=lambda x: x['publish_date_object'])

def add_all_vids_to_right_playlists(loaded_output_playlists, policy_context, playlist_settings, youtube_helper):
    num_added = 0
    for key in policy_context.keys():
        if key not in playlist_settings:
            raise Exception("Missing setting")
        num_added += _add_all_vids_to_playlist(loaded_output_playlists, policy_context[key], playlist_settings[key], youtube_helper)
    return num_added
