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
import csv


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


def copy_specific_files(file_names, source_folder, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    for file_name in file_names:
        source_path = os.path.join(source_folder, file_name)
        destination_path = os.path.join(destination_folder, file_name)
        shutil.copy2(source_path, destination_path)


def remove_non_utf8_characters(file_path):
    with open(file_path, 'rb') as file:
        filedata = file.read()
    # Decode UTF-8 while ignoring errors
    filedata = filedata.decode("utf-8", errors="ignore")
    # Remove non-ASCII characters
    filedata = re.sub(r'[^\x00-\x7F]+', ' ', filedata)
    # Write the file out again
    with open(file_path, 'w', encoding="utf8") as file:
        file.write(filedata)


def create_file(file_path, content):
    dir = os.path.dirname(file_path)
    if dir and not os.path.exists(dir):
        os.makedirs(dir)

    with open(file_path, 'w') as file:
        file.write(content)


def comment_matching_lines(filename, line_content):
    # Read the file
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Comment matching lines
    lines = ['//' + line if line.strip() == line_content else line for line in lines]

    # Write the file
    with open(filename, 'w') as file:
        file.writelines(lines)


def comment_java_test(filename, method_name):
    with open(filename, 'r') as file:
        lines = file.readlines()

    in_method = False
    brace_count = 0
    for i, line in enumerate(lines):
        # If line above method declaration contains "@Test"
        if i > 0 and "@Test" in lines[i-1]:
            lines[i-1] = '//' + lines[i-1]
        if re.search(r'(public|protected|private|static|\s) +[\w\<\>\[\]]+\s+%s\(' % re.escape(method_name), line):
            in_method = True
            found_first_open_brace = False
            lines[i] = '/*' + line
        if in_method:
            if not found_first_open_brace:
                if line.count('{') > 0:
                    found_first_open_brace = True
            brace_count += line.count('{')
            brace_count -= line.count('}')
            if brace_count == 0 and found_first_open_brace:
                lines[i] = line.strip() + '*/\n'
                break
    with open(filename, 'w') as file:
        file.writelines(lines)


def create_java_file(folder, filename, content):
    with open(f"{folder}/{filename}.java", 'w') as f:
        f.write(content)


def replace_string_in_file(file_path, string_to_replace, replacement_string):
    # Open the file in binary read mode
    with open(file_path, 'rb') as file:
        file_content = file.read()
        file.close()

    # Decode the file content and replace all occurrences of the string
    modified_content = file_content.decode('utf-8').replace(string_to_replace, replacement_string)

    # Encode the modified content back into bytes
    modified_content = modified_content.encode('utf-8')

    # Write the modified content back into the file in binary write mode
    with open(file_path, 'wb') as file:
        file.write(modified_content)
        file.flush()  # ensure all internal buffers associated with file are emptied
        os.fsync(file.fileno())  # ensure file is written to disk
        file.close()


def update_version_in_file(file_path, artifact_id, old_version, new_version):
    # Use 'rb' and 'wb' (read and write binary) to avoid problems with line endings
    with open(file_path, 'rb') as file:
        lines = file.readlines()
        file.close()

    # Convert the lines from bytes to string using the correct encoding
    lines = [line.decode('utf-8') for line in lines]

    for i in range(len(lines)):
        if artifact_id in lines[i] and old_version in lines[i + 1]:
            lines[i + 1] = lines[i + 1].replace(old_version, new_version)

    # Convert the lines from string back to bytes using the correct encoding
    lines = [line.encode('utf-8') for line in lines]

    with open(file_path, 'wb') as file:
        file.writelines(lines)
        file.flush()  # ensure all internal buffers associated with file are emptied
        os.fsync(file.fileno())  # ensure file is written to disk
        file.close()


def read_tests_file(file_path):
    tests = {
        "passing_tests": [],
        "failing_tests": [],
        "compilation_problems": []
    }
    first_row = True
    with open(os.path.join(file_path, "tests.csv"), 'r') as file:
        content = file.read().replace('\0', '')
        csv_reader = csv.reader(content.splitlines())
        for row in csv_reader:
            if first_row:
                first_row = False
                continue
            test_name = row[0]
            if row[1] == "PASS":
                tests["passing_tests"].append(test_name)
            else:
                if "compilation problem" in row[3].strip():
                    tests["compilation_problems"].append(test_name)
                else:
                    tests["failing_tests"].append(test_name)
    return tests


def bug_belongs_to_file(file_path, project, bug_id):
    data = json_file_to_dict(file_path)
    if project not in data.keys():
        return False
    if bug_id not in data[project].keys():
        return False
    return True



#%%
