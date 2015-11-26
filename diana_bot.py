# coding=utf-8
import logging
import datetime
import requests
import sys
import getopt
import re
import urllib
from credentials import SLACK_BOT_TOKEN,\
    JIRA_AUTHORIZATION,\
    JIRA_API_URL,\
    SLACK_CHANNEL_ID,\
    SLACK_BOT_NAME,\
    SPECIAL_VERSION_URL,\
    JIRA_PROJECT_NAME

days_count = {
    0: '6',
    1: '2',
    2: '3',
    3: '2',
    4: '3',
    5: '4',
    6: '5'
}

class JiraController():
    def __init__(self):
        logging.basicConfig(level = logging.INFO)

    def get_tickets(self, release_version):
        """
        Gets the finished tickets statistics
        """
        response = []
        params = self.get_params(release_version)

        finished_tickets = self.make_jira_request(params)

        for ticket in finished_tickets['issues']:
            response.append({
                "key" : ticket['key'],
                "desc" : ticket['fields']['summary']
            })

        return response

    def make_jira_request(self, params):
        headers = {
            'contentType': 'application/json',
            'Authorization': JIRA_AUTHORIZATION
        }

        response = requests.get(JIRA_API_URL,
            params = {
                'jql': 'project="' + params['project_name'] + '" AND "Preview branch" ~ "' + params['release_version'] + '"'
            },
            headers = headers).json()

        logging.info("\nFetching data from last " + params['days_before'] + " days for project " + params['project_name'])

        return response

    def get_params(self, release_version):
        today = datetime.datetime.today().weekday()
        params = {
            'project_name': JIRA_PROJECT_NAME,
            'days_before': days_count[today],
            'release_version': 'wikia:%s' % release_version
        }

        optlist, args = getopt.getopt(sys.argv[1:], "p:d:", ["project=", "days="])
        print optlist

        for option, arg in optlist:
            if option in ("-p", "--project") and arg != '--days':
                params['project_name'] = arg
            if option in ("-d", "--days") and arg.isdigit():
                params['days_before'] = arg

        return params


class SlackUpdater(object):
    SLACK_API_URL = 'https://slack.com/api/chat.postMessage'

    def __init__(self, slack_bot_token = None, slack_bot_channel = SLACK_CHANNEL_ID):
        assert slack_bot_token is not None
        assert slack_bot_channel is not None

        self.slack_bot_token = slack_bot_token
        self.slack_bot_channel = slack_bot_channel

    def post_slack_message(self, payload):
        response = requests.post(self.SLACK_API_URL,
                      data = {
                          'channel': self.slack_bot_channel,
                          'token': self.slack_bot_token,
                          'text': payload,
                          'username': SLACK_BOT_NAME
                      })

        logging.info("\nPosting to Slack: done")

    def prepare_slack_update(self, tickets, team = '*Content West- Wing*'):
        """
        Processes acquired results
        """
        if (len(tickets) == 0):
            return team + ' :Nothing user facing'

        result = '```'

        for ticket in tickets:
            result += 'https://wikia-inc.atlassian.net/browse/' + ticket['key'] + ' ' + ticket['desc'] + '\n'

        return result + '```'

class Wikia(object):
    def get_current_version(self):
        handler = urllib.urlopen(SPECIAL_VERSION_URL)
        html = handler.read()
        matches = re.search(r"(release-\d+)\.\d+", html, re.MULTILINE)
        assert matches is not None
        return matches.group(1)

if __name__ == "__main__":
    calculation = JiraController()
    slack_updater = SlackUpdater( slack_bot_token = SLACK_BOT_TOKEN )
    wikia = Wikia()

    tickets = calculation.get_tickets(wikia.get_current_version())
    release_update = slack_updater.prepare_slack_update(tickets)
    slack_updater.post_slack_message(release_update)
