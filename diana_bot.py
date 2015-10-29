# coding=utf-8

import logging
import time
import requests
import sys
from credentials import SLACK_BOT_TOKEN, JIRA_AUTHORIZATION, JIRA_API_URL

class InfobotxCalculation():
    def __init__(self):
        logging.basicConfig(level = logging.INFO)

    def get_tickets(self):
        """
        Gets the finished tickets statistics
        """
        response = []
        days_before = '2'

        if len(sys.argv) > 1 and sys.argv[1].isdigit() and sys.argv[1] > 0:
            days_before = str(sys.argv[1])

        finished_tickets = self.make_jira_request(days_before)

        for ticket in finished_tickets['issues']:
            response.append({
                "key" : ticket['key'],
                "desc" : ticket['fields']['summary']
            })

        return response

    def make_jira_request(self, days_before, project_name = 'Data / API'):
        headers = {
            'contentType': "application/json",
            "Authorization": JIRA_AUTHORIZATION
        }

        response = requests.get(JIRA_API_URL,
            params = {
                'jql': 'status in(Closed,Solved,Done) AND project="' + project_name + '" AND updated >= -' + days_before + 'd AND type != "Retrospective Action"'
            },
            headers = headers).json()

        return response


class SlackUpdater(object):
    SLACK_API_URL = 'https://slack.com/api/chat.postMessage'

    def __init__(self, slack_bot_token = None, slack_bot_channel = 'C0CLL8H8E'):
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
                          'username': 'West-wing updater'

                      })

        logging.info("\nPosting to Slack: done")

    def prepare_slack_update(self, tickets):
        """
        Processes acquired results
        """
        if (len(tickets) == 0):
            return '*Nothing user facing*'

        result = '```'

        for ticket in tickets:
            result += 'https://wikia-inc.atlassian.net/browse/'+ ticket['key'] + ' ' + ticket['desc'] + '\n'

        return result + '```'


if __name__ == "__main__":
    calculation = InfobotxCalculation()
    slack_updater = SlackUpdater( slack_bot_token = SLACK_BOT_TOKEN )

    tickets = calculation.get_tickets()
    release_update = slack_updater.prepare_slack_update(tickets)
    print release_update
    slack_updater.post_slack_message(release_update)
