# slack-jira-sprint-updates
Bot which posts on slack recently finished tickets.

## Setup
To use bot you need to create file credentials.py where you'll put:
```
JIRA_API_URL = ''
SLACK_BOT_TOKEN = ''
JIRA_AUTHORIZATION = ''
YOUR_CHANNEL_ID = ''
```

## Running
All you need to do is go to `slack-jira-sprint-updates` dir and run:

`python diana_bot.py`

For now, it by default assumes releases are on Tuesdays and Thursdays.

## Options
If you want to see tickets from last particular number of days, for example finished within last 10 days, run:

`python diana_bot.py 10`

