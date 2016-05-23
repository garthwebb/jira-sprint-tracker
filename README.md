# jira-sprint-tracker
Bot which pulls current sprint information and compiles statistics

## Setup
To use bot you need to create file credentials.py where you'll put:
```
SPECIAL_VERSION_URL = ''
JIRA_API_URL = ''
JIRA_AUTHORIZATION = ''
JIRA_PROJECT_NAME = ''
SLACK_CHANNEL_ID = ''
SLACK_BOT_TOKEN = ''
SLACK_BOT_NAME = ''
```

## Running
All you need to do is go to `jira-sprint-tracker` dir and run:

`python jira_bot.py`

For now, it by default assumes releases are on Tuesdays and Thursdays.

## Options
If you want to see tickets from last couple of days, for example finished within last 10 days, run:

`python jira_bot.py -d 10` or `python jira_bot.py --days 10`

If you want to see tickets from particular project, for example Social, run:

`python jira_bot.py -p Social` or `python jira_bot.py --project Social`

## Integration with Slack
Go to channel you want to add the bot to and click: `Add a service integration` -> `Bots` -> `Add bot integration` and you'll get your `SLACK_BOT_TOKEN` needed to post a message.

## Schedule it!
To run task periodically, every fixed amount of time, use `cron`.

For example, to run scrypt every week from Monday to Thursday at 4p.m.:

* run `crontab -e` on machine you want to run the script on.
* paste following line:

`0 16 * * 1-4 python ~/jira-sprint-tracker/jira_bot.py`

