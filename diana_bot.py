# coding=utf-8

import logging
import time
import requests
from credentials import SLACK_BOT_TOKEN, JIRA_AUTHORIZATION, JURA_API_URL

class InfobotxCalculation():
    def __init__(self):
        logging.basicConfig(level = logging.INFO)

    def get_tickets(self, days_before = '2', project_name = 'Data / API'):
        """
        Gets the finished tickets statistics
        """
        headers = {'contentType': "application/json", "Authorization": JIRA_AUTHORIZATION }
        response = []

        finised_tickets = requests.get(JURA_API_URL, params = {
            'jql': 'status in(Closed,Solved,Done) AND project="' + project_name + '" AND updated >= -' + days_before + 'd AND type != "Retrospective Action"'
        }, headers = headers).json()

        print finised_tickets['total']
        for ticket in finised_tickets['issues']:
            response.append({
                "key" : ticket['key'],
                "desc" : ticket['fields']['summary']
            })

        return response


class SlackUpdater(object):
    SLACK_API_URL = 'https://slack.com/api/chat.postMessage'

    def __init__(self, slack_bot_token = None, slack_bot_channel = 'C0CLL8H8E'):
        assert slack_bot_token is not None
        assert slack_bot_channel is not None

        self.slack_bot_token = slack_bot_token
        self.slack_bot_channel = slack_bot_channel

    def post_slack_message(self, payload):
        logging.info("Posting to Slack")
        response = requests.post(self.SLACK_API_URL,
                      data={
                          'channel': self.slack_bot_channel,
                          'token': self.slack_bot_token,
                          'text': payload,
                          'username': 'West-wing updater'

                      })
        #print response.json()
        logging.info("\nPost_slack_message: done")

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
    #print release_update
    slack_updater.post_slack_message(release_update)
