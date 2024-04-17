# Steam Family Notifier
This is a simple script that parses a Steam Family's combined library for new games, then sends a notification to a Discord webhook listing both the new games, and who added them.

This script is intended to be run on a local environment that you control, because it requires access to one of your Steam cookies.

![image](https://github.com/AriannaStory/SteamFamilyNotifier/assets/4652603/a56c2efc-3f76-4934-9f79-ff2d28e22328)

## Prerequisites
Ensure you have Python 3 installed on your machine. You can install all required libraries using:

```bash
pip install argparse datetime os pytz requests python-dateutil python-dotenv
```

# Configuration
All configuration for this script is done via `.env` file. You should rename the included `.env.example` file to `.env`.

| .env key    | Description |
| -------- | ------- |
| WEBAPI_KEY  | The Steam Web API key that you can get from https://steamcommunity.com/dev/apikey |
| COOKIE_TOKEN | See [the "Cookie Token" section](#cookie-token) below |
| DISCORD_WEBHOOK_URL    | The Discord webhook URL that you'd like to use (see [Discord's documentation](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks))    |
| DISCORD_WEBHOOK_USERNAME | The name that you'd like to appear with your Discord webhook |
| DISCORD_WEBHOOK_AVATAR_URL | The URL to the avatar image you'd like to appear with your Discord webhook |
| DEFAULT_DAY_COUNT | The number of days "back" that the script should look each time (default: 1) |

## Cookie Token
<a id="cookie-token"></a>
Unfortunately, the API that Steam uses to generate your family's game library is an undocumented one, and your regular Web API key will not work for it. Instead, you'll use a workaround by providing one of your cookies to this script. This is necessary because the "private" access token rotates every day, and otherwise you'd need to manually copy and paste your private access token into the script every day.

> [!CAUTION]
> **NEVER** give any of your Steam cookies to **anyone** else. Only use this script in an environment that *you* control entirely.<br>If anyone else has access to this cookie, **they will have access to your Steam account!**<br>If you still want to continue, you can click the statement below to open instructions:

<details>
<summary>I understand the danger of providing my Steam cookie to this script.</summary>

1. Navigate to [Steam's Points Summary Page](https://store.steampowered.com/pointssummary/ajaxgetasyncconfig).
2. Open Developer Tools in your browser (F12 or right-click -> Inspect), and switch to the "Application" tab.
3. Under "Storage", find and expand "Cookies", then select "https://store.steampowered.com".
4. Locate the `steamLoginSecure` cookie, copy its value, and paste it into your `.env` file under "COOKIE_TOKEN".

</details>

# Usage
Schedule `run.py` to run regularly based on your `DEFAULT_DAY_COUNT` to notify of new game additions automatically.

```bash
# To run the script:
python run.py

# To run the script and check for new games added in the past X days:
python run.py -d X

# To enable more verbose output for debugging:
python run.py -v
```

# Technical Details
We're using the following Steam APIs (thanks, [XPaw](https://xpaw.me/)!):
* [IFamilyGroupsService/GetSharedLibraryApps](https://steamapi.xpaw.me/#IFamilyGroupsService/GetSharedLibraryApps) (gets the shared library)
* [IFamilyGroupsService/GetFamilyGroupForUser](https://steamapi.xpaw.me/#IFamilyGroupsService/GetFamilyGroupForUser) (gets the family group you're in)
* [ISteamUser/GetPlayerSummaries](https://steamapi.xpaw.me/#ISteamUser/GetPlayerSummaries) (gets the username from a given Steam User ID)