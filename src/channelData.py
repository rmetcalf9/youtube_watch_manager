import json
import os
from watchPolicies import default_watch_policy, get_watch_policy

class ChannelData:
    data_file_name = None
    data = None
    default_max_seen_pub_date = None
    def __init__(self, data_file_name, default_max_seen_pub_date):
        self.data_file_name = data_file_name
        self.default_max_seen_pub_date = default_max_seen_pub_date
        self.data = {}
        if not os.path.isfile(data_file_name):
            print("No channel data file found - starting with no channel data")
        else:
            with open(self.data_file_name, "r") as fileHandle:
                self.data = json.load(fileHandle)

    def save_changes(self, channel_id=None):
        # if channel id is set we only have to save that channels data
        with open(self.data_file_name, "w") as fileHandle:
            fileHandle.write(json.dumps(self.data,indent=2))

    def get_data_for_channel(self, channel_name, channel_id):
        if channel_id not in self.data:
            self.data[channel_id] = {
                "channel_id": channel_id,
                "chanel_name": channel_name,
                "last_run_last_pub_data": self.default_max_seen_pub_date,
                "watch_policy": default_watch_policy
            }
            # Save the data on creation
            self.save_changes(channel_id=channel_id)
        return (
            self.data[channel_id]["last_run_last_pub_data"],
            get_watch_policy(self.data[channel_id]["watch_policy"])
        )

    def set_last_pub_data(self, channel_id, last_run_last_pub_data):
        self.data[channel_id]["last_run_last_pub_data"] = last_run_last_pub_data

    def reset_last_pub_dates(self):
        for channel_id in self.data.keys():
            self.data[channel_id]["last_run_last_pub_data"] = self.default_max_seen_pub_date
