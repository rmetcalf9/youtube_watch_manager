from ._BaseWatchPolicy import SaveAllToPlaylist
import constants

class SaveAllToWatchNow(SaveAllToPlaylist):
    def __init__(self, name, require_min_duration=True):
        super().__init__(playlist="watch_now", name=name, require_min_duration=require_min_duration)


