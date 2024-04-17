import argparse
import datetime
import os
import pytz
import requests
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
DISCORD_WEBHOOK_USERNAME = os.getenv('DISCORD_WEBHOOK_USERNAME')
DISCORD_WEBHOOK_AVATAR_URL = os.getenv('DISCORD_WEBHOOK_AVATAR_URL')
COOKIE_TOKEN = os.getenv('COOKIE_TOKEN')
WEBAPI_KEY = os.getenv('WEBAPI_KEY')
DEFAULT_DAY_COUNT = int(os.getenv('DEFAULT_DAY_COUNT', '1'))

def verbose_print(message, verbose):
    if verbose:
        print(message)

def get_username_from_id(id_key, webapi_key, verbose, username_cache):
    if id_key in username_cache:
        return username_cache[id_key], username_cache

    url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={webapi_key}&steamids={id_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        players = data.get('response', {}).get('players', [])
        if not players:
            verbose_print(f"[ERROR] No players found for ID {id_key}", verbose)
            return None, username_cache
        username = players[0].get('personaname')
        if username:
            username_cache[id_key] = username
            verbose_print(f"[INFO] Successfully cached Steam User ID {id_key} as {username}", verbose)
            return username, username_cache
    except requests.RequestException as e:
        verbose_print(f"[ERROR] Unable to retrieve user name for user {id_key}: {str(e)}", verbose)
        return None, username_cache

def fetch_webapi_token(cookie_token, verbose):
    url = 'https://store.steampowered.com/pointssummary/ajaxgetasyncconfig'
    cookies = {'steamLoginSecure': cookie_token}
    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()
        data = response.json()
        return data['data'].get('webapi_token')
    except requests.RequestException as e:
        verbose_print(f"[ERROR] Failed to retrieve WebAPI Token: {str(e)}", verbose)
        return None

def fetch_family_id(access_token, verbose):
    url = f'https://api.steampowered.com/IFamilyGroupsService/GetFamilyGroupForUser/v1/?access_token={access_token}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        family_id = data['response'].get('family_groupid')
        verbose_print(f"[INFO] Found family ID {family_id}", verbose)
        return family_id
    except requests.RequestException as e:
        verbose_print(f"[ERROR] Failed to retrieve the family ID: {str(e)}", verbose)
        return None

def fetch_steam_library(access_token, family_id, verbose):
    if not access_token or not family_id:
        return None
    api_url = f'https://api.steampowered.com/IFamilyGroupsService/GetSharedLibraryApps/v1/?access_token={access_token}&family_groupid={family_id}&include_own=true'
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        verbose_print("[INFO] Successfully loaded the Steam family library...", verbose)
        return response.json()
    except requests.RequestException as e:
        verbose_print(f"[ERROR] Failed to fetch data: {str(e)}", verbose)
        return None

def send_discord_notification(new_games, days, discord_webhook_url, discord_webhook_username, discord_webhook_avatar_url, webapi_key, verbose, username_cache):
    if not new_games:
        verbose_print(f"[INFO] No new games added in the last {days} day(s).", verbose)
        return username_cache
    verbose_print(f"[INFO] Found {len(new_games)} new games in the library from the last {days} days...", verbose)
    new_games.sort(key=lambda x: x['name']) # Sort alphabetically
    intro_content = f"Great news; {len(new_games)} new games were added to the Family Library in the last {days} day(s)!"
    max_length = 2000 - 100 # Discord character limit per-message for webhooks, with a 100 character buffer
    
    game_lines = []
    for game in new_games:
        owner_id = game['owner_steamids'][0]
        username, username_cache = get_username_from_id(owner_id, webapi_key, verbose, username_cache)
        verbose_print(f"[INFO] Found {game['name']} (added by {username})", verbose)
        line = f"* [{game['name']}](<http://store.steampowered.com/app/{game['appid']}>) by {username if username else 'Unknown user'}"
        game_lines.append(line)

    messages = []
    current_message = ""
    for line in game_lines:
        if len(current_message) + len(line) + 1 > max_length:
            messages.append(current_message)
            current_message = line + "\n"
        else:
            current_message += line + "\n"
    if current_message:
        messages.append(current_message)

    for i, msg in enumerate(messages):
        content = f"{intro_content}\n\n{msg}" if i == 0 else f"{msg}"
        payload = {
            "content": content,
            "username": discord_webhook_username,
            "avatar_url": discord_webhook_avatar_url
        }
        try:
            response = requests.post(discord_webhook_url, json=payload)
            if response.status_code != 204:
                verbose_print("[ERROR] Failed to send notification: " + str(response.status_code), verbose)
        except requests.RequestException as e:
            verbose_print(f"[ERROR] Error sending Discord notification: {str(e)}", verbose)
    verbose_print(f"[INFO] Successfully sent Discord notifications...", verbose)
    return username_cache


def main(days, verbose, discord_webhook_url, discord_webhook_username, discord_webhook_avatar_url, cookie_token, webapi_key):
    username_cache = {}
    webapi_token = fetch_webapi_token(cookie_token, verbose)
    family_id = fetch_family_id(webapi_token, verbose) if webapi_token else None
    library_data = fetch_steam_library(webapi_token, family_id, verbose) if family_id else None
    if library_data:
        apps = library_data['response']['apps']
        eastern = pytz.timezone('US/Eastern')
        past_date = datetime.datetime.now(eastern) - datetime.timedelta(days=days)
        new_games = [app for app in apps if datetime.datetime.fromtimestamp(app['rt_time_acquired'], tz=eastern) > past_date]
        send_discord_notification(new_games, days, discord_webhook_url, discord_webhook_username, discord_webhook_avatar_url, webapi_key, verbose, username_cache)
    verbose_print("[INFO] Exiting script...", verbose)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and notify about new games from the Steam Family library.")
    parser.add_argument('-d', '--days', type=int, default=DEFAULT_DAY_COUNT, help="Number of days to look back for new games.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Shows verbose information about the script running.")
    args = parser.parse_args()
    main(args.days, args.verbose, DISCORD_WEBHOOK_URL, DISCORD_WEBHOOK_USERNAME, DISCORD_WEBHOOK_AVATAR_URL, COOKIE_TOKEN, WEBAPI_KEY)
