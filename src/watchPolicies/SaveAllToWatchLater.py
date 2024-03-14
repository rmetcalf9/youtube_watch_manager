from ._BaseWatchPolicy import BaseWatchPolicy
import constants

class SaveAllToWatchLater(BaseWatchPolicy):
    require_min_duration=None
    def __init__(self, name, require_min_duration=True):
        self.require_min_duration = require_min_duration
        super().__init__(name=name)
    def requires_duration(self):
        return self.require_min_duration
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        if self.require_min_duration:
            if duration < constants.MINIMUM_DURATION_VID_IN_SECONDS:
                return
        self._add_to_context(policy_context, video_id, video_title, publish_date_object, "watch_later")

