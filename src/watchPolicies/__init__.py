from googleapiclient import errors

ONE_HOUR_IN_SECONDS = 60 * 60
THRITY_MINUTES_IN_SECONDS = 60 * 30

class BaseWatchPolicy():
    name = None
    def __init__(self, name):
        self.name = name
    def requires_duration(self):
        return False
    def assign_vid_to_playlist(self, video_id, duration, policy_context):
        raise Exception("Policy not implemented")
    def _add_to_context(self, policy_context, video_id, video_title, publish_date_object, list):
        policy_context[list].append({
            "id": video_id,
            "title": video_title,
            "publish_date_object": publish_date_object
        })

class SplitBetweenWatchLaterAndLongWatchLater(BaseWatchPolicy):
    divide_point = None
    def __init__(self, divide_point, name):
        self.divide_point=divide_point
        super().__init__(name=name)
    def requires_duration(self):
        return True
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        if duration < self.divide_point:
            self._add_to_context(policy_context, video_id, video_title, publish_date_object, "watch_later")
        else:
            self._add_to_context(policy_context, video_id, video_title, publish_date_object, "long_watch_later")

class WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour(BaseWatchPolicy):
    def __init__(self):
        super().__init__(name="WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour")
    def requires_duration(self):
        return True
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        if duration < ONE_HOUR_IN_SECONDS:
            self._add_to_context(policy_context, video_id, video_title, publish_date_object, "watch_later")
        else:
            pass

class SaveAllToWatchLater(BaseWatchPolicy):
    def __init__(self):
        super().__init__(name="SaveAllToWatchLater")
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        self._add_to_context(policy_context, video_id, video_title, publish_date_object, "watch_later")

class SaveAllToWatchNow(BaseWatchPolicy):
    def __init__(self):
        super().__init__(name="SaveAllToWatchNow")
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        self._add_to_context(policy_context, video_id, video_title, publish_date_object, "watch_now")

_watch_policies = []
_watch_policies.append(SplitBetweenWatchLaterAndLongWatchLater(divide_point=ONE_HOUR_IN_SECONDS, name="WatchPolicySaveLessThanHourToWatchLater"))
_watch_policies.append(SplitBetweenWatchLaterAndLongWatchLater(divide_point=THRITY_MINUTES_IN_SECONDS, name="WatchPolicySaveLessThan30MinutesToWatchLater"))
_watch_policies.append(SaveAllToWatchLater())
_watch_policies.append(SaveAllToWatchNow())
_watch_policies.append(WatchPolictSaveLessThanHourToWatchLaterIgnoreMoreThanAnHour())

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
