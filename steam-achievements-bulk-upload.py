import os
import re
import json
import requests
import sys

# Usage: python3 steam-achievements-bulk-upload.py ach_data.json images_dir steam_apps.json cookie.txt
#   - ach_data.json     : see below for format
#   - images_dir        : path to where the achievement icons specified in ach_data.json are
#   - steam_apps.json   : Steam application id collecation
#   - cookie.txt        : taken from the browser (Inspector/Network) after loggin in. 
#                   Must include params like sessionid, steamLoginSecure, steamMachineAuth.
#                   eg: "requestedPrimaryPublisher=999; steamLoginSecure=76...; sessionid=eb...; steamMachineAuth76..."
# ach_data.json format:
# {
#     "data": [
#         {
#             "id": "",
#             "icon": "filename.jpg",
#             "icon_locked": "filename.jpg",
#             "name": {
#                 "en": "Name"
#             },
#             "description": {
#                 "en": "Description"
#             }
#         }
#     ]
# }

DELETE_ALL_MODE = False
DEBUG = False

LOCALE_MAP = {
    'ar': "arabic",
    'bg': "bulgarian",
    'cs': "czech",
    'da': "danish",
    'de': "german",
    'el': "greek",
    'en': "english",
    'es': "spanish",
    'fi': "finnish",
    'fr': "french",
    'hu': "hungarian",
    'it': "italian",
    'ja': "japanese",
    'ko': "koreana",
    'nl': "dutch",
    'no': "norwegian",
    'pl': "polish",
    'pt': "portuguese",
    'pt-BR': "brazilian",
    'ro': "romanian",
    'ru': "russian",
    'sv': "swedish",
    'th': "thai",
    'tr': "turkish",
    'uk': "ukrainian",
    'zh-Hans': "schinese",
    'zh-Hant': "tchinese"
}


def get_session_id(cookie):
    match = re.search(r'sessionid=([\w\d]+);', cookie)
    if match:
        return match.group(1)
    raise ValueError("sessionid not found in cookie.")


def steam_request(url, cookie, data=None, files=None):
    headers = {"cookie": cookie}
    if data:
        response = requests.post(url, headers=headers, data=data, files=files)
    else:
        response = requests.get(url, headers=headers)
    if DEBUG:
        print(f"Request to {url} -> {response.text}")
    return response.json()


def fetch_achievements(app_id, cookie):
    url = f'https://partner.steamgames.com/apps/fetchachievements/{app_id}'
    return steam_request(url, cookie)


def new_achievement(app_id, session_id, statid, bitid, cookie):
    url = f'https://partner.steamgames.com/apps/newachievement/{app_id}'
    data = {'sessionid': session_id, 'maxstatid': statid, 'maxbitid': bitid}
    return steam_request(url, cookie, data)

def delete_achievement(app_id, session_id, statid, bitid, cookie):
    url = f'https://partner.steamgames.com/apps/deleteachievement/{app_id}/{statid}/{bitid}'
    data = {'sessionid': session_id}
    return steam_request(url, cookie, data)

def save_achievement(app_id, session_id, statid, bitid, apiname, names, descs, hidden, permission, progressStat, progressMin, progressMax, cookie):
    url = f'https://partner.steamgames.com/apps/saveachievement/{app_id}'
    displayname = {LOCALE_MAP[loc]: names[loc] for i, loc in enumerate(names.keys())}
    description = {LOCALE_MAP[loc]: descs[loc] for i, loc in enumerate(descs.keys())}
    displayname['token'] = f'NEW_ACHIEVEMENT_{statid}_{bitid}_NAME'
    description['token'] = f'NEW_ACHIEVEMENT_{statid}_{bitid}_DESC'

    data = {
        'sessionid': session_id,
        'statid': statid,
        'bitid': bitid,
        'apiname': apiname,
        'displayname': json.dumps(displayname),
        'description': json.dumps(description),
        'permission': permission,
        'hidden': "true" if hidden else "false",
        'progressStat': progressStat,
        'progressMin': progressMin,
        'progressMax': progressMax
    }

    return steam_request(url, cookie, data)


def upload_image(app_id, session_id, statid, bitid, locked, filename, cookie):
    url = 'https://partner.steamgames.com/images/uploadachievement'
    request_type = 'achievement_gray' if locked else 'achievement'
    files = {'image': open(filename, 'rb')}
    data = {
        'sessionid': session_id,
        'MAX_FILE_SIZE': '3000000',
        'appID': app_id,
        'statID': statid,
        'bit': bitid,
        'requestType': request_type
    }
    return steam_request(url, cookie, data, files)


def main(ach_data_file, img_path, steam_apps, cookie):
    with open(ach_data_file, 'r') as achievements_file:
        data = json.load(achievements_file)

    with open(steam_apps, 'r') as steam_apps_file:
        steam_apps_data = json.load(steam_apps_file)

    with open(cookie, 'r') as cookie_file:
        cookie = cookie_file.read()

    session_id = get_session_id(cookie)

    for app in steam_apps_data["steam_apps"]:
        app_id = app["id"]
        app_name = app["name"]
        print(f"Processing achievements for {app_name} ({app_id})")

        achievements = fetch_achievements(app_id, cookie)

        existing_achievements = {
            ach['api_name']: ach for ach in achievements['achievements']
        }

        for ach in data['data']:
            ach_id = ach['id']
            if ach_id in existing_achievements:
                # Can be optimized by checking if it has changed before updating. The tricky part for this is checking if the images have changed.
                print(f"Updating achievement {ach_id} for App ID {app_id}")
                existing_ach = existing_achievements[ach_id]

                # Preserve existing stat_id and bit_id
                statid = existing_ach['stat_id']
                bitid = existing_ach['bit_id']

                # Update the achievement data
                save_achievement(
                    app_id, session_id, statid, bitid,
                    ach_id, ach['name'], ach['description'],
                    ach['hidden'], ach['permission'],
                    ach.get('progressStat', ""), ach.get('progressMin', ""), ach.get('progressMax', ""),
                    cookie
                )

                # Upload images only if they have changed (optional)
                upload_image(app_id, session_id, statid, bitid, False, os.path.join(img_path, ach['icon']), cookie)
                upload_image(app_id, session_id, statid, bitid, True, os.path.join(img_path, ach['icon_locked']), cookie)

            else:
                print(f"Creating new achievement {ach_id} for App ID {app_id}")
                statid, bitid = max(
                    (ach['stat_id'], ach['bit_id']) for ach in achievements['achievements']
                )
                bitid += 1

                result = new_achievement(app_id, session_id, statid, bitid, cookie)
                statid = result['achievement']['stat_id']
                bitid = result['achievement']['bit_id']

                save_achievement(
                    app_id, session_id, statid, bitid,
                    ach_id, ach['name'], ach['description'],
                    ach['hidden'], ach['permission'],
                    ach.get('progressStat', ""), ach.get('progressMin', ""), ach.get('progressMax', ""),
                    cookie
                )

                upload_image(app_id, session_id, statid, bitid, False, os.path.join(img_path, ach['icon']), cookie)
                upload_image(app_id, session_id, statid, bitid, True, os.path.join(img_path, ach['icon_locked']), cookie)

    print("All achievements processed.")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python upload_steam_achievements.py ach_data.json images_dir steam_apps.json cookie.txt")
        sys.exit(1)
    main(*sys.argv[1:])
