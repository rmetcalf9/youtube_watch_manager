from google_client import GoogleClient, YoutubeApiHelpers
import json
from googleapiclient.discovery import build

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
        subs = self.youtube_helper.get_subscriptions()
        for sub in subs:
            print(sub["snippet"]["title"])
