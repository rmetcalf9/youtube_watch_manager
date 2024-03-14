
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
