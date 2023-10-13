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

    def _get_full_list(self, fn, part, mine=None, channel_id=None, id=None, playlist_id=None, min_content_details_vid_pub_date=None):
        if min_content_details_vid_pub_date is not None:
            min_content_details_vid_pub_date_obj = parse(min_content_details_vid_pub_date)
        ret_val = []
        pageToken = None
        args = {
            "part": part
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
                if latest_time_in_results < min_content_details_vid_pub_date_obj:
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
                raise Exception("Either choos My channel or supply an id - not both")
        chan_info_resp = self._get_full_list(
            fn=self.youtube_service.channels,
            part=part,
            id=channel_id,
            mine=mine
        )
        print("EE", chan_info_resp)
        raise Exception("DD")

    def get_video_uploads_for_channel(self, channel_id, min_content_details_vid_pub_date, playlist_item_part="contentDetails"):
        min_content_details_vid_pub_date_obj = parse(min_content_details_vid_pub_date)

        channel_info = self._get_full_list(
            fn=self.youtube_service.channels,
            part="contentDetails",
            id=channel_id
        )
        if len(channel_info)!=1:
            raise DidNotFindChannelException("Wrong number of results")
        upload_playlist_id = channel_info[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        # print("PL ID=", upload_playlist_id)
        playlist_items = self.get_playlistitems(
            playlist_id=upload_playlist_id,
            part=playlist_item_part,
            min_content_details_vid_pub_date=min_content_details_vid_pub_date
        )
        playlist_items_after_min_date = []
        for item in playlist_items:
            item_publish_time = parse(item["contentDetails"]["videoPublishedAt"])
            if item_publish_time > min_content_details_vid_pub_date_obj:
                playlist_items_after_min_date.append(item)
        return playlist_items_after_min_date

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
        try:
            vals = self._get_full_list(
                fn=self.youtube_service.playlistItems,
                part=part,
                mine=None,
                playlist_id=playlist_id,
                min_content_details_vid_pub_date=min_content_details_vid_pub_date
            )
        except errors.HttpError:
            return []
        return vals

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

    def insert_video_into_playlist(self, video_id, playlist_id):
        body = {
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }
        request = self.youtube_service.playlistItems().insert(part="snippet", body=body)
        response=request.execute()
