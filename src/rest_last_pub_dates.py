from appObj import appObj


# https://developers.google.com/youtube/v3/code_samples/code_snippets
settings_file_name="./settings.json"

global_account_data = None
global_settings = None

if __name__ == '__main__':
    appObj = appObj(settings_file_name=settings_file_name)

    print("Start")

    appObj.reset_last_pub_dates()

    print("End")
    exit(0)
