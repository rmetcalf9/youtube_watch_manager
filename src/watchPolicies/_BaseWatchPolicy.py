import constants

class BaseWatchPolicy():
    name = None
    def __init__(self, name):
        self.name = name
    def requires_duration(self):
        return False
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        raise Exception("Policy not implemented")
    def _add_to_context(self, policy_context, video_id, video_title, publish_date_object, list):
        policy_context[list].append({
            "id": video_id,
            "title": video_title,
            "publish_date_object": publish_date_object
        })

class SaveAllToPlaylist(BaseWatchPolicy):
    require_min_duration=None
    playlist = None
    def __init__(self, playlist, name, require_min_duration=True):
        self.playlist = playlist
        self.require_min_duration = require_min_duration
        super().__init__(name=name)
    def requires_duration(self):
        return self.require_min_duration
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        if self.require_min_duration:
            if duration < constants.MINIMUM_DURATION_VID_IN_SECONDS:
                return
        self._add_to_context(policy_context, video_id, video_title, publish_date_object, self.playlist)

