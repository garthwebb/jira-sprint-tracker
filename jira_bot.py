# coding=utf-8
import logging
import datetime
import json
import requests
import sys
import getopt
import os.path

from credentials import\
    SLACK_BOT_TOKEN,\
    JIRA_AUTHORIZATION,\
    JIRA_API_SEARCH_URL,\
    SLACK_CHANNEL_ID,\
    SLACK_BOT_NAME,\
    JIRA_PROJECT_NAME


class JiraController:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def get_tickets(self):
        """
        Gets the finished tickets statistics
        """
        response = []
        params = self.get_params()

        finished_tickets = self.make_jira_request(params)

        for ticket in finished_tickets['issues']:
            fields = ticket.get('fields')
            assignee = fields.get('assignee')
            if assignee:
                assignee_name = assignee.get('name')
            else:
                assignee_name = ''

            response.append({
                "key": ticket['key'],
                "assignee": assignee_name,
                "status": fields['status']['name'],
            })

        return response

    @staticmethod
    def make_jira_request(params):
        headers = {
            'contentType': 'application/json',
            'Authorization': JIRA_AUTHORIZATION
        }

        jql = 'project="{}" and Sprint in openSprints()'.format(params['project_name'])

        response = requests.get(JIRA_API_SEARCH_URL,
                                params={'jql': jql},
                                headers=headers).json()

        logging.info("\nFetching data for project {}".format(params['project_name']))

        return response

    @staticmethod
    def get_params():
        params = {
            'project_name': JIRA_PROJECT_NAME,
        }

        optlist, args = getopt.getopt(sys.argv[1:], "p:", ["project="])
        print optlist

        for option, arg in optlist:
            if option in ("-p", "--project") and arg != '--days':
                params['project_name'] = arg

        return params

class JiraIssue(object):
    expand = ''
    id = ''
    selfUrl = ''
    key = ''
    fields = dict()
    changelog = object

    def __init__(self, data):
        self.expand = data.get('expand')
        self.id = data.get('id')
        self.selfUrl = data.get('selfUrl')
        self.key = data.get('key')

        for fieldName in data.get('fields'):
            value = data.get('fields').get(fieldName)
            self.fields[fieldName] = JiraIssueField(fieldName, value)

        self.changelog = JiraIssueChangelog(data.get('changelog'))


class JiraIssueField(object):

    def __init__(self, name, value):
        self.name = name
        self.value = value

class JiraIssueChangelog(object):

    def __init__(self, log):
        self.log = log

class SlackUpdater(object):
    SLACK_API_URL = 'https://slack.com/api/chat.postMessage'

    def __init__(self, slack_bot_token=None, slack_bot_channel=SLACK_CHANNEL_ID):
        assert slack_bot_token is not None
        assert slack_bot_channel is not None

        self.slack_bot_token = slack_bot_token
        self.slack_bot_channel = slack_bot_channel

    def post_slack_message(self, payload):
        response = requests.post(self.SLACK_API_URL,
                                 data={
                                     'channel': self.slack_bot_channel,
                                     'token': self.slack_bot_token,
                                     'text': payload,
                                     'username': SLACK_BOT_NAME
                                 })

        logging.info("\nPosting to Slack: done")

    @staticmethod
    def prepare_slack_update(tickets, team='*Content West- Wing*'):
        """
        Processes acquired results
        :param team:
        :param tickets:
        """
        if len(tickets) == 0:
            return team + ' :Nothing user facing'

        result = '```'

        for ticket in tickets:
            result += 'https://wikia-inc.atlassian.net/browse/' + ticket['key'] + ' ' + ticket['desc'] + '\n'

        return result + '```'


class TicketLogger:
    BASE_PATH = '/tmp/jira-bot/'

    def update(self, tickets):
        for t in tickets:
            filename = self.BASE_PATH + t['key']

            data = []
            if os.path.exists(filename):
                target = open(filename, 'r')
                try:
                    data = json.load(target)
                except ValueError:
                    pass

                target.close()

            # If there's data and the last status line and assignee is unchanged, skip it
            if len(data) > 0:
                last_item = data[-1]
                if last_item['status'] == t['status'] and last_item['assignee'] == t['assignee']:
                    continue

            t['ts'] = datetime.datetime.now().strftime("%c")
            data.append(t)

            target = open(filename, 'w+')
            json.dump(data, target)
            target.close()


if __name__ == "__main__":
    calculation = JiraController()
    slack_updater = SlackUpdater(slack_bot_token=SLACK_BOT_TOKEN)
    logger = TicketLogger()

    tickets = calculation.get_tickets()
    logger.update(tickets)


    #pprint(tickets)
    #release_update = slack_updater.prepare_slack_update(tickets)
    #slack_updater.post_slack_message(release_update)
