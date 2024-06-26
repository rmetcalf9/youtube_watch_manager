from google_client import GoogleClient, YoutubeApiHelpers, YoutubeApiHelpersDidNotFindChannelException
import json
from googleapiclient.discovery import build
from dateutil.parser import parse
from channelData import ChannelData
import isodate
from watchPolicies import get_policy_initial_context, add_all_vids_to_right_playlists, sort_policy_context
from functools import reduce
import datetime
import pytz

class appObj():
    settings = None
    youtube_helper = None
    channel_Data = None
    settings_file_name = None

    def __init__(self, settings_file_name):
        self.settings = None
        self.settings_file_name = settings_file_name
        with open(self.settings_file_name, "r") as fileHandle:
            self.settings = json.load(fileHandle)

        #example default_max_seen_pub_date "2023-10-01T01:00:15Z"
        default_max_seen_pub_date = self.settings["default_max_seen_pub_date"]
        if default_max_seen_pub_date.upper().strip() == "TODAY":
            default_max_seen_pub_date = datetime.datetime.now(pytz.timezone("UTC")).isoformat()

        self.channel_data = ChannelData(self.settings["channel_data_file"], default_max_seen_pub_date)
        self.channel_data.save_backup(self.settings["channel_data_backup_file"])

        google_client = GoogleClient( self.settings["google_credentials_file"], self.settings["temporary_token_file"])
        creds = google_client.get_creds()
        self.youtube_helper = YoutubeApiHelpers(build('youtube', 'v3', credentials=creds))

        self._populate_playlist_ids()

    def get_video_durations(self, video_ids):
        ret_dat = {}
        video_batch_information = self.youtube_helper.get_video_information(
            video_ids=video_ids,
            part="contentDetails,snippet"
        )
        for video_inforamtion in video_batch_information:
            # Saving the duration of each vid in seconds
            if "duration" not in video_inforamtion["contentDetails"]:
                if video_inforamtion["snippet"]["liveBroadcastContent"] == "upcoming":
                    print("Upcomming live broadcast detected - not adding vids form this channel")
                    return None
            ret_dat[video_inforamtion["id"]] = isodate.parse_duration(video_inforamtion["contentDetails"]["duration"]).total_seconds()
        return ret_dat

    def _print_results(self, policy_context):
        for x in policy_context.keys():
            if len(policy_context[x])==0:
                print(f"{x}- None")
            else:
                for vid_info in policy_context[x]:
                    print(f"{x}- {vid_info['title']}")

    def _process_subscription(self, channel_id, sub, policy_context):
        (last_run_last_pub_date, watch_policy) = self.channel_data.get_data_for_channel(
            channel_name=sub['snippet']['title'],
            channel_id=channel_id
        )
        print(
            f"Collecting unwatched videos from {sub['snippet']['title']} - adding all published after {last_run_last_pub_date}")

        playlist = []
        try:
            playlist = self.youtube_helper.get_video_uploads_for_channel(
                channel_id=channel_id,
                min_content_details_vid_pub_date=last_run_last_pub_date,
                playlist_item_part="contentDetails,snippet"  # id,status not needed
            )
        except YoutubeApiHelpersDidNotFindChannelException:
            print("Channel may be unavailable")
            return

        last_run_last_pub_date_parsed = parse(last_run_last_pub_date)
        batch_size = self.settings["list_vid_from_channel_batch_size"]
        vids_in_channel = playlist.get_items()
        while vids_in_channel:
            chunk, vids_in_channel = vids_in_channel[:batch_size], vids_in_channel[batch_size:]
            durations = {}
            if watch_policy.requires_duration():
                video_ids = []
                for vid in chunk:
                    video_ids.append(vid["contentDetails"]["videoId"])
                durations = self.get_video_durations(video_ids=video_ids)
                if durations is None:
                    # returning here skips updating the channel last update
                    return {
                        "live_content": True
                    }


            for vid in chunk:
                video_id = vid["contentDetails"]["videoId"]
                duration = None
                if watch_policy.requires_duration():
                    duration = durations[video_id]

                pub_date = parse(vid["contentDetails"]["videoPublishedAt"])
                if pub_date > last_run_last_pub_date_parsed:
                    last_run_last_pub_date_parsed = pub_date
                    last_run_last_pub_date = vid["contentDetails"]["videoPublishedAt"]
                video_title = vid["snippet"]["title"]

                #print(f"videoId {video_id} published {vid['contentDetails']['videoPublishedAt']} title {video_title} duration {duration}")
                watch_policy.assign_vid_to_playlist(
                    video_id=video_id,
                    video_title=video_title,
                    publish_date_object=pub_date,
                    duration=duration,
                    policy_context=policy_context
                )
        self.channel_data.set_last_pub_data(channel_id, last_run_last_pub_date)

    def ensure_subs_in_channel_data(self, subs):
        for sub in subs:
            (_, _) = self.channel_data.get_data_for_channel(
                channel_name=sub['snippet']['title'],
                channel_id=sub["snippet"]["resourceId"]["channelId"],
                save_changes=False
            )
        self.channel_data.save_changes()

    def load_output_playlist(self):
        ret_val = {}
        for playlist_key in self.settings["playlists"].keys():
            ret_val[self.settings["playlists"][playlist_key]["id"]] = self.youtube_helper.get_playlistitems(
                playlist_id=self.settings["playlists"][playlist_key]["id"],
                min_content_details_vid_pub_date=self.settings["system_playlist_max_seen_pub_date"], # for my playlists get all the vids
                part="contentDetails,id,snippet,status"
            )
        return ret_val

    def run(self):
        loaded_output_playlists = self.load_output_playlist()

        subs = self.youtube_helper.get_subscriptions()
        self.ensure_subs_in_channel_data(subs=subs)
        removed_subs = self.get_list_of_removed_subs(subs=subs)
        print("These channels are no longer subscribed to:")
        for sub in removed_subs:
            print(" - ", sub["chanel_name"])
        print("")
        summary_total_vids_added = 0
        summary_channels_with_live_content = []
        for sub in subs:
            total_vids_added = 0
            if sub["snippet"]["resourceId"]["kind"] != "youtube#channel":
                raise Exception("NI - not a channel")
            channel_id = sub["snippet"]["resourceId"]["channelId"]

            policy_context = get_policy_initial_context()
            process_subscription_return = self._process_subscription(channel_id=channel_id, sub=sub, policy_context=policy_context)
            if process_subscription_return is not None:
                if "live_content" in process_subscription_return:
                    if process_subscription_return["live_content"]:
                        summary_channels_with_live_content.append(sub["snippet"]["title"])
            sort_policy_context(policy_context)
            self._print_results(policy_context)
            total_vids_added += add_all_vids_to_right_playlists(
                loaded_output_playlists=loaded_output_playlists,
                policy_context=policy_context,
                playlist_settings=self.settings["playlists"],
                youtube_helper=self.youtube_helper
            )
            all_vids = []
            for playlist_key in policy_context.keys():
                all_vids += policy_context[playlist_key]

            print("Total vids added=", total_vids_added)
            print("")
            summary_total_vids_added += total_vids_added
            self.channel_data.save_changes(channel_id=channel_id)
            #raise Exception("Stop after single subscription")
            #if total_vids_added>0:
            #    raise Exception("Stop after single subscription that actually added vids")

        print("--------------")
        print("--------------")
        print(" full summary")
        print("--------------")
        print("--------------")
        print("summary_total_vids_added", summary_total_vids_added)
        if len(summary_channels_with_live_content) > 0:
            print("Channels with live content")
            for chan in summary_channels_with_live_content:
                print(chan)


    def reset_last_pub_dates(self):
        self.channel_data.reset_last_pub_dates()
        self.channel_data.save_changes()

        settings_changed = False
        for playlist in self.settings["playlists"].keys():
            if "id" in self.settings["playlists"][playlist]:
                del self.settings["playlists"][playlist]["id"]
                settings_changed = True
        if settings_changed:
            self.save_settings()

    def save_settings(self):
        with open(self.settings_file_name, "w") as fileHandle:
            fileHandle.write(json.dumps(self.settings, indent=2))

    def _we_need_to_populate_some_ids(self):
        for playlist in self.settings["playlists"].keys():
            if not "id" in self.settings["playlists"][playlist]:
                return True
        return False

    def _populate_playlist_ids(self):
        if self._we_need_to_populate_some_ids():
            youtube_playlist_sanitized_name_map = {}
            playlists = self.youtube_helper.get_my_playlists(part="snippet")
            for playlist in playlists:
                if playlist["kind"]=="youtube#playlist":
                    playlist_sanitized = playlist["snippet"]["title"].strip().lower()
                    youtube_playlist_sanitized_name_map[playlist_sanitized] = playlist["id"]
            for playlist in self.settings["playlists"].keys():
                if not "id" in self.settings["playlists"][playlist]:
                    playlist_name_sanitized = self.settings["playlists"][playlist]["name"].strip().lower()
                    if playlist_name_sanitized not in youtube_playlist_sanitized_name_map:
                        if playlist_name_sanitized=="Watch Later".strip().lower():
                            self.settings["playlists"][playlist]["id"] = "WL"
                        else:
                            raise Exception("Invalid playlist name", self.settings["playlists"][playlist]["name"])
                    else:
                        self.settings["playlists"][playlist]["id"] = youtube_playlist_sanitized_name_map[playlist_name_sanitized]
            self.save_settings()

    def get_list_of_removed_subs(self, subs):
        retVal = []

        subed_titles = []
        for sub in subs:
            subed_titles.append(sub["snippet"]["title"])

        for chanel_key in self.channel_data.data.keys():
           if self.channel_data.data[chanel_key]["chanel_name"] not in subed_titles:
               retVal.append(self.channel_data.data[chanel_key])

        return retVal

