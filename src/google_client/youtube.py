import copy

from dateutil.parser import parse
from googleapiclient import errors

#https://developers.google.com/youtube/v3/docs

class DidNotFindChannelException(Exception):
    pass

#Members of  youtube_service
# ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__enter__', '__eq__', '__exit__',
# '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__',
# '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__',
# '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__',
# '__weakref__', '_add_basic_methods', '_add_nested_resources', '_add_next_methods', '_baseUrl',
# '_developerKey', '_dynamic_attrs', '_http', '_model', '_requestBuilder', '_resourceDesc',
# '_rootDesc', '_schema', '_set_dynamic_attr', '_set_service_methods', 'abuseReports', 'activities',
# 'captions', 'channelBanners', 'channelSections', 'channels', 'close', 'commentThreads', 'comments',
# 'i18nLanguages', 'i18nRegions', 'liveBroadcasts', 'liveChatBans', 'liveChatMessages', 'liveChatModerators',
# 'liveStreams', 'members', 'membershipsLevels', 'new_batch_http_request', 'playlistItems', 'playlists',
# 'search', 'subscriptions', 'superChatEvents', 'tests', 'thirdPartyLinks', 'thumbnails',
# 'videoAbuseReportReasons', 'videoCategories', 'videos', 'watermarks', 'youtube']



class YoutubeApiHelpers():
    youtube_service = None
    def __init__(self, youtube_service):
        self.youtube_service = youtube_service

    def _get_full_list(
        self,
        fn,
        part,
        mine=None,
        channel_id=None,
        id=None,
        playlist_id=None,
        min_content_details_vid_pub_date=None,
        max_results=50
    ):
        if min_content_details_vid_pub_date is not None:
            min_content_details_vid_pub_date_obj = parse(min_content_details_vid_pub_date)
        ret_val = []
        pageToken = None
        args = {
            "part": part,
            "maxResults": max_results
        }
        if channel_id is not None:
            args["channelId"] = channel_id
        if id is not None:
            args["id"] = id
        if mine is not None:
            args["mine"] = mine
        if playlist_id is not None:
            args["playlistId"] = playlist_id

        while True:
            args["pageToken"] = pageToken
            request = fn().list(**args)
            response = request.execute()
            if "items" not in response:
                break
            for ite in response["items"]:
                ret_val.append(ite)

            if "nextPageToken" not in response:
                pageToken = None
            else:
                pageToken = response["nextPageToken"]
            if pageToken is None:
                break
            if min_content_details_vid_pub_date is not None:
                if len(response["items"])==0:
                    break
                latest_time_in_results = parse(response["items"][-1]["contentDetails"]["videoPublishedAt"])
                if latest_time_in_results <= min_content_details_vid_pub_date_obj:
                    break

        return ret_val

    def get_subscriptions(self, part="snippet"):  #part="snippet,contentDetails"
        return self._get_full_list(
            fn=self.youtube_service.subscriptions,
            mine=True,
            part=part
        )

    def get_channel_info(self, channel_id=None, mine=True, part="contentDetails"):
        if mine:
            if channel_id is not None:
                raise Exception("Either choose My channel or supply an id - not both")
        chan_info_resp = self._get_full_list(
            fn=self.youtube_service.channels,
            part=part,
            id=channel_id,
            mine=mine
        )
        return chan_info_resp

    def get_video_uploads_for_channel(self, channel_id, min_content_details_vid_pub_date, playlist_item_part="contentDetails"):
        channel_info = self._get_full_list(
            fn=self.youtube_service.channels,
            part="contentDetails",
            id=channel_id
        )
        if len(channel_info)!=1:
            raise DidNotFindChannelException("Wrong number of results")
        upload_playlist_id = channel_info[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        # print("PL ID=", upload_playlist_id)
        return self.get_playlistitems(
            playlist_id=upload_playlist_id,
            part=playlist_item_part,
            min_content_details_vid_pub_date=min_content_details_vid_pub_date
        )

    def get_playlist_info(self, playlist_id, part):
        vals = self._get_full_list(
            fn=self.youtube_service.playlists,
            part=part,
            mine=None,
            id=playlist_id
        )
        if len(vals)!=1:
            raise Exception("Wrong number of results")
        return vals[0]

    def get_playlistitems(self, playlist_id, min_content_details_vid_pub_date, part="contentDetails,id,snippet,status"):
        return YoutubePlaylist(
            self,
            playlist_id=playlist_id,
            min_content_details_vid_pub_date=min_content_details_vid_pub_date,
            part=part
        )

    def get_playlists_for_channel(self, channel_id, part="snippet,contentDetails"):
        return self._get_full_list(
            fn=self.youtube_service.playlists,
            part=part,
            mine=None,
            id=channel_id
        )

    def get_my_playlists(self, part="snippet,contentDetails"):
        return self._get_full_list(
            fn=self.youtube_service.playlists,
            part=part,
            mine=True
        )

    def get_video_information(self, video_ids, part="contentDetails"):
        return self._get_full_list(
            fn=self.youtube_service.videos,
            part=part,
            mine=None,
            id=",".join(video_ids)
        )

class YoutubePlaylist():
    youtube_api_helpers = None
    playlist_id = None
    min_content_details_vid_pub_date = None
    part = None

    items = None

    def __init__(
        self,
        youtube_api_helpers,
        playlist_id,
        min_content_details_vid_pub_date,
        part="contentDetails,id,snippet,status"
    ):
        self.youtube_api_helpers = youtube_api_helpers
        self.playlist_id = playlist_id
        self.min_content_details_vid_pub_date = min_content_details_vid_pub_date
        self.part = part

        response = []
        try:
            response = self.youtube_api_helpers._get_full_list(
                fn=self.youtube_api_helpers.youtube_service.playlistItems,
                part=part,
                mine=None,
                playlist_id=playlist_id,
                min_content_details_vid_pub_date=min_content_details_vid_pub_date
            )
        except errors.HttpError:
            response = []

        min_content_details_vid_pub_date_obj = parse(self.min_content_details_vid_pub_date)

        self.items = []
        for item in response:
            item_publish_time = parse(item["contentDetails"]["videoPublishedAt"])
            if item_publish_time > min_content_details_vid_pub_date_obj:
                self.items.append(item)

    def contains_video(self, video_id):
        for ite in self.items:
            if ite["snippet"]["resourceId"]["videoId"]==video_id:
                return True
        return False

    def insert_video(self, video_id):
        if self.contains_video(video_id=video_id):
            print("Video already in list - not calling API")
            return 0
        body = {
            'snippet': {
                'playlistId': self.playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        request = self.youtube_api_helpers.youtube_service.playlistItems().insert(part="snippet", body=body)
        response=request.execute()

        #TODO Check response code

        return 1

    def get_items(self):
        return copy.deepcopy(self.items)

{'kind': 'youtube#playlistItem', 'etag': 'hpCbazrY7iJCpDkX5qI0pvLTt_c', 'id': 'UEwyRmZHckRUYkVpOWFEaVdOSFVnTUtNZC1UVFlVbVViNC41NkI0NEY2RDEwNTU3Q0M2',
 'snippet': {'publishedAt': '2023-10-16T13:27:59Z', 'channelId': 'UCvxXC-IoIPadPYRJ7hZIoVw',
             'title': "Revealing Multi-Millionaire Property Investor's WORST Deal",
             'description': "Join Samuel Leeds Property Crash Course for £1: https://www.property-investors.co.uk/?ref=226\n\nRevealing Multi-Millionaire Property Investor's WORST Deal\n\nShare this video: [video link goes here]\n\n🎥 How to build a property portfolio from scratch in 7 DAYS: https://youtu.be/RWEkj1y8XKs\n\n📖 My favourite book: https://amzn.to/39VcYLa\n\n❓ Have a question about property? Join my Property Facebook Group: https://www.facebook.com/groups/778613042238071\n\n🗣️FOLLOW ME ON SOCIAL MEDIA:\nInstagram: https://www.instagram.com/samuelleedsofficial/\nFacebook Group: https://www.facebook.com/groups/778613042238071\nFacebook Page: https://www.facebook.com/OfficialSamuelLeeds/\nTwitter: https://twitter.com/samuel_leeds\nLinkedIn: https://www.linkedin.com/in/samuel-leeds-64660683\n\nFor collaboration enquires please email marketing@samuelleeds.com\n\n🔔 Subscribe for daily content: https://www.youtube.com/SamuelLeeds?sub_confirmation=1\n\n*WARNING* Samuel Leeds will never give out his number in the comments of this YouTube channel. There is currently a channel impersonating Samuel Leeds and commenting on videos with a number to message about investing in cryptocurrencies so please beware of this. \n\n #PropertyInvesting",
             'thumbnails': {
                 'default': {
                     'url': 'https://i.ytimg.com/vi/OyivdWh9pSo/default.jpg', 'width': 120, 'height': 90},
                      'medium': {'url': 'https://i.ytimg.com/vi/OyivdWh9pSo/mqdefault.jpg', 'width': 320, 'height': 180},
                 'high': {'url': 'https://i.ytimg.com/vi/OyivdWh9pSo/hqdefault.jpg', 'width': 480, 'height': 360},
                 'standard': {'url': 'https://i.ytimg.com/vi/OyivdWh9pSo/sddefault.jpg', 'width': 640, 'height': 480},
                 'maxres': {'url': 'https://i.ytimg.com/vi/OyivdWh9pSo/maxresdefault.jpg', 'width': 1280, 'height': 720}},
             'channelTitle': 'Robert Metcalf', 'playlistId': 'PL2FfGrDTbEi9aDiWNHUgMKMd-TTYUmUb4', 'position': 0,
             'resourceId': {'kind': 'youtube#video', 'videoId': 'OyivdWh9pSo'},
             'videoOwnerChannelTitle': 'Samuel Leeds', 'videoOwnerChannelId': 'UCS6SES6btXx2tVFzWy4oToA'}, 'contentDetails': {'videoId': 'OyivdWh9pSo', 'videoPublishedAt': '2023-10-15T16:00:22Z'}, 'status': {'privacyStatus': 'public'}}
