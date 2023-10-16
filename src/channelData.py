import json
import os
from watchPolicies import default_watch_policy, get_watch_policy
from dateutil.parser import parse

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

    def save_backup(self, backup_file_name):
        with open(backup_file_name, "w") as fileHandle:
            fileHandle.write(json.dumps(self.data,indent=2))

    def get_data_for_channel(self, channel_name, channel_id, save_changes=True):
        if channel_id not in self.data:
            self.data[channel_id] = {
                "channel_id": channel_id,
                "chanel_name": channel_name,
                "last_run_last_pub_data": self.default_max_seen_pub_date,
                "watch_policy": default_watch_policy
            }
            # Save the data on creation
            if save_changes:
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

    def get_max_last_run_last_pub_data(self):
        ret_val = self.data[list(self.data.keys())[0]]["last_run_last_pub_data"]
        for channel in self.data.keys():
            if parse(self.data[channel]["last_run_last_pub_data"]) > parse(ret_val):
                ret_val = self.data[channel]["last_run_last_pub_data"]
        return ret_val


