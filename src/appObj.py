from google_client import GoogleClient, YoutubeApiHelpers, YoutubeApiHelpersDidNotFindChannelException
import json
from googleapiclient.discovery import build
from dateutil.parser import parse

class appObj():
    settings = None
    youtube_helper = None

    def __init__(self, settings_file_name):
        self.settings = None
        with open(settings_file_name, "r") as fileHandle:
            self.settings = json.load(fileHandle)

        google_client = GoogleClient( self.settings["google_credentials_file"], self.settings["temporary_token_file"])
        creds = google_client.get_creds()
        self.youtube_helper = YoutubeApiHelpers(build('youtube', 'v3', credentials=creds))


    def run(self):
        this_run_max_pub_date_obj = parse(self.settings["max_seen_pub_date"])

        subs = self.youtube_helper.get_subscriptions()
        for sub in subs:
            # channel_id = sub["snippet"]["channelId"] This is MY id
            if sub["snippet"]["resourceId"]["kind"] != "youtube#channel":
                raise Exception("NI - not a channel")
            channel_id = sub["snippet"]["resourceId"]["channelId"]

            print(f"Collecting unwatched videos from {sub['snippet']['title']}")


            # getting channel info for watch history
            my_channel_info = self.youtube_helper.get_channel_info(
                part="contentDetails,id,snippet,statistics,status,topicDetails"
            )
            #auditDetails

            raise Exception("TODO")

            vids_in_channel = []
            try:
                vids_in_channel = self.youtube_helper.get_video_uploads_for_channel(
                    channel_id=channel_id,
                    min_content_details_vid_pub_date=self.settings["max_seen_pub_date"]
                    #,playlist_item_part="contentDetails,id,snippet,status"
                )
            except YoutubeApiHelpersDidNotFindChannelException:
                print("Channel may be unavailiable")

            for vid in vids_in_channel:
                pub_date = parse(vid["contentDetails"]["videoPublishedAt"])
                if pub_date > this_run_max_pub_date_obj:
                    this_run_max_pub_date_obj = pub_date
                print("v", vid)
            raise Exception("FFF")

        print("TODO Save settings with pub date", this_run_max_pub_date_obj.isoformat())




