

class YoutubeApiHelpers():
    youtube_service = None
    def __init__(self, youtube_service):
        self.youtube_service = youtube_service

    def get_subscriptions(self, part="snippet"):
        ret_val = []
        pageToken = None
        while True:
            request = self.youtube_service.subscriptions().list(
                part=part, #"snippet,contentDetails",
                mine=True,
                pageToken=pageToken
            )
            response = request.execute()
            for ite in response["items"]:
                ret_val.append(ite)

            if "nextPageToken" not in response:
                pageToken = None
            else:
                pageToken = response["nextPageToken"]
            if pageToken is None:
                break

        return ret_val
