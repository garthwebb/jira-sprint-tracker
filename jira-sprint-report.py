# coding=utf-8
import logging
import re
import requests
import sys
import getopt
import datetime
from dateutil.parser import parse

from credentials import \
    JIRA_AUTHORIZATION,\
    JIRA_API_SEARCH_URL,\
    JIRA_API_ISSUE_URL,\
    JIRA_PROJECT_NAME


class JiraController:
    epics = dict()

    def __init__(self):
        logging.basicConfig(level=logging.INFO)

    def get_epic(self, issue):
        if not issue:
            return

        if issue in self.epics:
            return self.epics[issue]

        params = self.get_params()
        params['issue'] = issue

        response = self.make_issue_request(params)
        epic = JiraIssue(response)
        self.epics[issue] = epic

        return epic

    def get_issues(self):
        """
        Gets the finished tickets statistics
        """
        response = []
        params = self.get_params()

        finished_issues = self.make_jira_request(params)

        for issue_data in finished_issues['issues']:
            iss = JiraIssue(issue_data)

            if not iss.finished_in_sprint(params['sprint_name']):
                continue

            response.append(iss)

        return response

    def get_comments(self, issue):
        params = self.get_params()
        params['resource'] = 'comment'
        params['issue'] = issue

        response = self.make_issue_request(params)
        return JiraIssueComments(response)


    @staticmethod
    def make_issue_request(params):
        headers = {
            'contentType': 'application/json',
            'Authorization': JIRA_AUTHORIZATION
        }

        url = JIRA_API_ISSUE_URL
        if 'resource' in params:
            url = url + '/' + params['resource']

        response = requests.get(url.format(params['issue']),
                                headers=headers).json()

        return response

    @staticmethod
    def make_jira_request(params):
        headers = {
            'contentType': 'application/json',
            'Authorization': JIRA_AUTHORIZATION
        }

        status = 'Closed'
        skip_resolution = '"Cannot Reproduce", Duplicate, "Won\'t Do", "Won\'t Fix"'

        jql = 'project={} and Sprint="{}" and status={} and resolution not in ({})'.format(
                params['project_name'],
                params['sprint_name'],
                status,
                skip_resolution
        )

        response = requests.get(JIRA_API_SEARCH_URL,
                                params={'jql': jql, 'expand': 'changelog'},
                                headers=headers).json()

        logging.info("\nFetching data for project {}".format(params['project_name']))

        return response

    @staticmethod
    def get_params():
        params = {
            'project_name': JIRA_PROJECT_NAME,
        }

        optlist, args = getopt.getopt(sys.argv[1:], "p:s:", ["project=", "sprint="])

        for option, arg in optlist:
            if option in ("-p", "--project"):
                params['project_name'] = arg
            if option in ("-s", "--sprint"):
                params['sprint_name'] = arg

        return params


class JiraIssue(object):

    def __init__(self, data):
        self.expand = data.get('expand')
        self.id = data.get('id')
        self.self_url = data.get('selfUrl')
        self.key = data.get('key')
        self.fields = dict()

        for field_name in data.get('fields'):
            value = data.get('fields').get(field_name)
            self.fields[field_name] = JiraIssueField(field_name, value)

        self.changelog = JiraIssueChangelog(data.get('changelog'))

    def finished_in_sprint(self, sprint_name):
        """
        Returns true if the sprint name given was the most recent sprint for this issue
        :param sprint_name: Sprint name string
        :return: boolean for whether this issue was finished in the sprint given
        """
        sprints = self.get_sprints()

        if sprints:
            return sprints[-1] == sprint_name
        else:
            return False

    def field(self, field_name):
        return self.fields[field_name].value

    def get_time_in_status(self, status_name):
        status_changes = self.changelog.get_status_change('')

        cumulative = datetime.timedelta()
        last_time = 0
        for change in status_changes:
            # Find the status item
            for item in change['items']:
                if item['field'] == 'status':
                    status_item = item
                    break

            if status_item and status_item['toString'] == status_name:
                last_time = parse(change['created'])
            else:
                if last_time != 0:
                    cumulative += parse(change['created']) - last_time
                    last_time = 0

        seconds = int(cumulative.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds %= 60

        return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    def get_sprints(self):
        sprints = self.field(JiraIssueField.FIELD_SPRINT)
        sprint_names = dict()

        for sprint_info in sprints:
            match = re.search('name=([^,]+).+sequence=([0-9]+)', sprint_info)
            if not match:
                continue

            name = match.group(1)
            sequence = match.group(2)
            sprint_names[sequence] = name

        return [value for (key, value) in sorted(sprint_names.items())]

    def get_developer(self):
        in_progress = self.changelog.get_status_change('In Progress')
        if in_progress:
            return self.get_developer_from_event(in_progress[0])
        else:
            return ''

#        if len(in_progress) == 1:
#            return self.get_developer_from_event(in_progress[0])
#        else:
#            return self.get_developer_from_comments()

    @staticmethod
    def get_developer_from_event(event):
        event_assignee = event['author']['name']

        # If we find an assignee item, use this as the author instead
        for item in event['items']:
            if item['field'] == 'assignee':
                event_assignee = item['to']

        return event_assignee

    def get_developer_from_comments(self):
        jira = JiraController()
        comments = jira.get_comments(self.key)

        pr_comments = comments.find_comments("https://github\.com/Wikia/app/pull")
        if pr_comments:
            return pr_comments[-1]['author']['name']
        else:
            return ''


class JiraIssueField(object):
    FIELD_SPRINT = 'customfield_10007'
    FIELD_STORY_POINTS = 'customfield_10004'
    FIELD_EPIC_LINK = 'customfield_10200'
    FIELD_EPIC_NAME = 'customfield_10201'

    def __init__(self, name, value):
        self.name = name
        self.value = value


class JiraIssueChangelog(object):

    def __init__(self, log):
        self.log = log

    def get_history(self):
        return self.log['histories']

    def get_status_change(self, status):
        history = self.get_history()

        status_events = list()
        for event in history:

            for item in event['items']:
                if item['field'] != 'status':
                    continue

                if status and status != item['toString']:
                    continue

                status_events.append(event)

        return status_events


class JiraIssueComments(object):

    def __init__(self, comments):
        self.comments = comments

    def find_comments(self, containing):
        matches = []

        for comment in self.comments:
            match = re.search(containing, comment)
            if match:
                matches.append(comment)

        return matches


if __name__ == "__main__":
    jira = JiraController()
    params = jira.get_params();
    sprint_name = params['sprint_name']

    issues = jira.get_issues()

    print "Key\tStory Points\tDeveloper\tTime in Dev\tSprint\tEpic Link"
    for issue in issues:
        epic_link = issue.field(JiraIssueField.FIELD_EPIC_LINK)
        if epic_link:
            epic = jira.get_epic(epic_link)
            if epic:
                epic_name = epic.field(JiraIssueField.FIELD_EPIC_NAME)
            else:
                print "Can't find epic for {}".format(epic_link)
                epic_name = 'None'
        else:
            epic_name = 'None'

        print("{}\t{}\t{}\t{}\t{}\t{}".format(
                issue.key,
                issue.field(JiraIssueField.FIELD_STORY_POINTS),
                issue.get_developer(),
                issue.get_time_in_status('In Progress'),
                ", ".join(issue.get_sprints()),
                epic_name
        ))
