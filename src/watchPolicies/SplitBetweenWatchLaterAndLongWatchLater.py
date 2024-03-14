from ._BaseWatchPolicy import BaseWatchPolicy
import constants

class SplitBetweenWatchLaterAndLongWatchLater(BaseWatchPolicy):
    require_min_duration=None
    divide_point = None
    def __init__(self, divide_point, name, require_min_duration=True):
        self.divide_point=divide_point
        self.require_min_duration = require_min_duration
        super().__init__(name=name)
    def requires_duration(self):
        return True
    def assign_vid_to_playlist(self, video_id, video_title, publish_date_object, duration, policy_context):
        if self.require_min_duration:
            if duration < constants.MINIMUM_DURATION_VID_IN_SECONDS:
                return
        if duration < self.divide_point:
            self._add_to_context(policy_context, video_id, video_title, publish_date_object, "watch_later")
        else:
            self._add_to_context(policy_context, video_id, video_title, publish_date_object, "long_watch_later")

