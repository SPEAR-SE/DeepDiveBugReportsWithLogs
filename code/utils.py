import re
import os
import json
import fnmatch
import requests
from urllib.parse import urlparse, quote
from secrets import github_token
from datetime import datetime, timezone
from git import Repo
from datetime import datetime
import shutil


def json_file_to_dict(file_path):
    data = {}
    with open(os.path.join(file_path), 'r', encoding='utf-8') as fp:
        data = json.load(fp)
    fp.close()
    return data


def find_regex_and_add_results_to_dict(regex, text, results_dict, key):
    regex_results = re.finditer(regex, text, re.MULTILINE)
    if regex_results:
        for log in regex_results:
            if key not in results_dict.keys():
                results_dict[key] = []
            results_dict[key].append(log.group())


def dict_to_json_file(file_path, dic):
    folder = os.path.dirname(file_path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(file_path, 'w') as fp:
        json.dump(dic, fp, sort_keys=True, indent=4)
    fp.close()


def find_folder_in_path(folder, path):
    pattern = fnmatch.translate(folder.lower())
    results = []
    for root, dirs, files in os.walk(path):
        for name in dirs:
            if fnmatch.fnmatch(name, pattern):
                results.append(os.path.join(root, name))
    return results


def find_file_in_path(file_name, path):
    for root, dirs, files in os.walk(path):
        if file_name in files:
            return os.path.join(root, file_name)


def read_file_lines(file_name, path):
    path = find_file_in_path(file_name, path)
    if path:
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
        file.close()
        return lines
    return []


def extract_creation_date_from_github_issues(url):
    path = urlparse(url).path
    api_url = "https://api.github.com/repos" + path
    headers = {
        "Authorization": "token {}".format(github_token),
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        creation_date = data.get('created_at', None)
        return creation_date
    elif response.status_code == 403:
        print('Rate limit exceeded. Please wait and try again.')
    elif response.status_code == 404:
        print('Issue not found.')
    else:
        print(f'Unexpected status code: {response.status_code}')

    return None


def extract_creation_date_from_jira(url):
    ticket_id = urlparse(url).path.split('/')[-1]
    api_url = f"https://issues.apache.org/jira/rest/api/2/issue/{quote(ticket_id)}"
    headers = {
        "Accept": "application/json"
    }
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        creation_date = data['fields']['created']
        return convert_date_format(creation_date)
    return None


def extract_creation_date_from_google_code(url):
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        first_comment = next((comment for comment in data['comments'] if comment['id'] == 0), None)
        # The first comment is actually the report body
        if first_comment:
            creation_date = datetime.fromtimestamp(first_comment['timestamp'])
            return creation_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def convert_date_format(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    dt = dt.replace(tzinfo=timezone.utc)  # Ensures the datetime object is in UTC
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_first_commit_before_date(repo_path, date_str, master_branch):
    repo = Repo(repo_path)
    date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

    # Get all commits before the given date
    commits_before_date = [c for c in repo.iter_commits(master_branch) if c.committed_date < date.timestamp()]

    # Check if there are any commits before the date
    if commits_before_date:
        # Return the hash of the first commit before the given date
        return commits_before_date[0].hexsha
    else:
        return None


def copy_folder_contents(source_folder, destination_folder):
    if not os.path.isdir(source_folder):
        print(f"Source folder '{source_folder}' does not exist.")
        return False
    try:
        shutil.copytree(source_folder, destination_folder)
        return True
    except Exception as e:
        print(f"An error occurred while copying folder contents: {str(e)}")
        return False


