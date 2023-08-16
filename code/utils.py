import re
import os
import json
import fnmatch
import requests
from urllib.parse import urlparse, quote
from datetime import timezone
from git import Repo
from datetime import datetime
import shutil
import csv
import sys

sys.path.append('../DeepDiveBugReportsWithLogs')
from my_secrets import github_token


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
    return None


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
        if i > 0 and "@Test" in lines[i - 1]:
            lines[i - 1] = '//' + lines[i - 1]
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


def bug_belongs_to_file(file_path, project, bug_id):
    data = json_file_to_dict(file_path)
    if project not in data.keys():
        return False
    if bug_id not in data[project].keys():
        return False
    return True


def get_modified_line_numbers_github_lib(patch):
    added_line_numbers = []
    deleted_line_numbers = []
    lines = patch.split('\n')
    current_line_number = None
    current_removed_line_number = None

    for line in lines:
        if line.startswith("@@"):
            current_line_number = int(line.split(' ')[2].split(',')[0][1:])
            current_removed_line_number = int(line.split(' ')[1].split(',')[0][1:])
        elif line.startswith('+') and not line.startswith('+++'):
            added_line_numbers.append(current_line_number)
            current_line_number += 1
        elif line.startswith('-') and not line.startswith('---'):
            deleted_line_numbers.append(current_removed_line_number)
            current_removed_line_number += 1
        elif line.startswith(' '):
            current_line_number += 1
            current_removed_line_number += 1

    return added_line_numbers, deleted_line_numbers


def get_modified_line_numbers_git_cli(lines):
    file_line_numbers = {}
    current_file = None
    current_line_number = None
    current_removed_line_number = None

    for line in lines:
        if line.startswith("diff --git"):
            current_file = line.split(" ")[-1].strip()
            file_line_numbers[current_file] = {"added": [], "deleted": []}
        elif line.startswith("@@"):
            current_line_number = int(line.split(' ')[2].split(',')[0][1:])
            current_removed_line_number = int(line.split(' ')[1].split(',')[0][1:])
        elif line.startswith('+') and not line.startswith('+++'):
            if not line.lstrip('+').lstrip().isspace() and line.lstrip('+').lstrip() != '':
                file_line_numbers[current_file]["added"].append(current_line_number)
            if current_line_number is not None:
                current_line_number += 1
        elif line.startswith('-') and not line.startswith('---'):
            if not line.lstrip('-').lstrip().isspace() and line.lstrip('-').lstrip() != '':
                file_line_numbers[current_file]["deleted"].append(current_removed_line_number)
            if current_removed_line_number is not None:
                current_removed_line_number += 1
        elif line.startswith(' '):
            if current_line_number is not None:
                current_line_number += 1
            if current_removed_line_number is not None:
                current_removed_line_number += 1

    return file_line_numbers


def extract_file_method_and_line_from_a_stack_trace_entry(stack_trace_entry):
    file_name = None
    method_name = None
    file_line = -1

    match = re.search(r'\s*at\s+([\w.$<>]+)\(([^:]*\.java):(\d+)\)', stack_trace_entry)
    if match:
        method_name = match.group(1)
        file_name = match.group(2)
        file_line = int(match.group(3))

    return file_name, method_name, file_line


def read_matrix_file(file_path):
    statements_covered_per_test = []
    test_passed = []

    with open(os.path.join(file_path, "matrix.txt"), 'r') as f:
        for line in f:
            row = [int(num) for num in line.strip()[:-1].split()]
            sign = line.strip()[-1]
            statements_covered_per_test.append(row)
    return statements_covered_per_test


def read_spectra_file(file_path):
    lines_of_code_obj_list = []
    pattern = r'^(.*?)#(.*?)\((.*?)\):(\d+)$'
    with open(os.path.join(file_path, "spectra.csv"), 'r') as file:
        first_line = True
        for line in file:
            # Skip the first line
            if first_line:
                first_line = False
                continue
            composed_str = line
            match = re.search(pattern, composed_str)
            if match is None:
                print("match not found")
                print(composed_str)
                continue
            class_name = match.group(1)
            method_name = match.group(2)
            method_parameters = match.group(3)
            line_number = int(match.group(4))
            lines_of_code_obj_list.append({
                "class_name": class_name,
                "method_name": method_name,
                "method_parameters": method_parameters,
                "line_number": line_number,
            })
    return lines_of_code_obj_list


def read_tests_file_and_classify_per_status(file_path):
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


def read_tests_file(file_path):
    test_names = []
    test_results = []
    first_row = True
    with open(os.path.join(file_path, "tests.csv"), 'r') as file:
        content = file.read().replace('\0', '')
        csv_reader = csv.reader(content.splitlines())
        for row in csv_reader:
            if first_row:
                first_row = False
                continue
            test_name = row[0]
            test_result = False
            if row[1] == "PASS":
                test_result = True
            test_names.append(test_name)
            test_results.append(test_result)
    return test_names, test_results


def read_file_lines_from_path(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        lines = [line.strip() for line in file.readlines()]
    file.close()
    return lines


def count_lines_of_code_for_coverage(file_path, project_path, covered_lines, begin_line=1, end_line=-1):
    path = os.path.join(project_path, file_path)
    lines = read_file_lines_from_path(path)
    if not lines:
        return 0
    if end_line == -1:
        end_line = len(lines)
    count = 0
    multiline_comment_active = False
    begin_pos = begin_line - 1
    end_pos = end_line - 1

    for i in range(begin_pos, end_pos + 1):
        line = lines[i]

        # If it is covered, it is a code line
        if i + 1 in covered_lines:
            count += 1
            continue

        # Ignore blocks inside multiline comments
        if line.strip().startswith("/*"):
            multiline_comment_active = True
            continue
        if multiline_comment_active:
            if line.strip().endswith("*/"):
                multiline_comment_active = False
            continue
        # Ignore single line comments
        if line.strip().startswith("//"):
            continue

        # Remove end-ine comments
        line = line.split("//")[0]
        # Count non-empty lines
        if line.strip() != "":
            # Ignoring closing braces only lines
            if line.strip() == "}":
                continue

            # Ignoring conditional lines (branches)
            if line.replace(" ", "").startswith("if") or line.replace("}", "").replace(" ", "").startswith("else"):
                continue

            # Ignoring loop definition lines
            if line.replace(" ", "").startswith("for") or line.replace(" ", "").startswith("while"):
                continue

            # Ignoring try-catch lines
            if line.replace(" ", "").startswith("try") or line.replace("}", "").replace(" ", ""). \
                    startswith("catch") or line.replace("}", "").replace(" ", "").startswith("finally"):
                continue

            # Treating statements with line break
            if line.strip().endswith("{") or line.strip().endswith("}") or line.strip(). \
                    endswith(";") or line.strip().endswith(","):
                count = count + 1

    return count


def create_coverage_percent_file(obj, output_file_path):
    with open(output_file_path, 'w') as file:
        # create the csv writer object
        csv_writer = csv.writer(file)
        csv_writer.writerow(["Project", "Bug_id", "Average_coverage_buggy_files",
                             "Average_coverage_stack_trace_files", "Average_all_files_coverage",
                             "Average_buggy_methods_coverage",
                             "Average_st_methods_coverage",
                             "Pos_first_buggy_method_in_stack_trace"])
        for project in obj.keys():
            for bug_id in obj[project].keys():
                csv_writer.writerow([project, bug_id,
                                     obj[project][bug_id]["average_coverage_buggy_files"],
                                     obj[project][bug_id]["average_coverage_stack_trace_files"],
                                     obj[project][bug_id]["average_all_files_coverage"],
                                     obj[project][bug_id]["average_buggy_methods_coverage"],
                                     obj[project][bug_id]["average_st_methods_coverage"],
                                     obj[project][bug_id]["pos_first_buggy_method_in_stack_trace"]])
    file.close()


def get_method_covered_lines_list(buggy_file_covered_lines, start_line, end_line):
    method_covered_lines = []
    for line in buggy_file_covered_lines:
        if start_line <= line <= end_line:
            method_covered_lines.append(line)
    return method_covered_lines


def find_file(file_name, path):
    # Iterate through all the subdirectories in the path
    for root, _, _ in os.walk(path):
        # Create the full path to the file by joining the current root with the relative name
        full_path = os.path.join(root, file_name)
        if os.path.exists(full_path):
            return os.path.abspath(full_path)
    return None


def get_bug_report_commit(data, project, bug_id):
    bug_data = data[project][bug_id]
    if "bug_report_commit_hash_ASE_paper" in bug_data.keys():
        return bug_data["bug_report_commit_hash_ASE_paper"]
    return bug_data["bug_report_commit_hash"]


def get_list_of_bugs_with_coverage(data):
    bugs_list = list(
        data["bugs_with_stack_traces"][
            "bugs_without_failing_tests_in_commons_with_defects4j"].keys()) + \
                list(data["bugs_with_stack_traces"][
                         "bugs_with_failing_tests_in_commons_with_defects4j"].keys())
    return bugs_list


def write_matrix_to_file(matrix, filename):
    with open(filename, 'w') as f:
        for row in matrix:
            f.write(' '.join(str(cell) for cell in row) + '\n')


def write_strings_list_to_csv(strings, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["name"])
        for string in strings:
            writer.writerow([string])


def write_two_lists_to_csv(list1, list2, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        for item1, item2 in zip(list1, list2):
            writer.writerow([item1, item2])


def store_methods_coverage_in_file(coverage, project, bug_id, gzoltar_files_path, file_name):
    project_gzoltar_folder = os.path.join(gzoltar_files_path, project)
    bug_gzoltar_folder = os.path.join(project_gzoltar_folder, bug_id)

    methods_coverage_matrix = coverage["methods_covered_per_test"]
    methods_coverage_matrix_file_name = os.path.join(bug_gzoltar_folder, "methods_matrix.txt")
    write_matrix_to_file(methods_coverage_matrix, methods_coverage_matrix_file_name)

    methods_spectra = coverage["methods_obj_list"]
    methods_coverage_matrix_file_name = os.path.join(bug_gzoltar_folder, "methods_spectra.csv")
    write_strings_list_to_csv(methods_spectra, methods_coverage_matrix_file_name)

    test_names = coverage["test_names"]
    fake_test_results_ochiai_1 = coverage["test_results"]
    fake_test_results_ochiai_1_file_name = os.path.join(bug_gzoltar_folder, file_name)
    write_two_lists_to_csv(test_names, fake_test_results_ochiai_1, fake_test_results_ochiai_1_file_name)


def read_methods_matrix_file(file_path):
    statements_covered_per_test = []
    with open(os.path.join(file_path, "methods_matrix.txt"), 'r') as f:
        for line in f:
            row = [int(num) for num in line.strip().split()]
            statements_covered_per_test.append(row)
    return statements_covered_per_test


def read_methods_spectra_file(file_path):
    lines_of_code_obj_list = []
    with open(os.path.join(file_path, "methods_spectra.csv"), 'r') as file:
        first_line = True
        for line in file:
            # Skip the first line
            if first_line:
                first_line = False
                continue
            lines_of_code_obj_list.append(line.replace("\n", ""))
    return lines_of_code_obj_list


def convert_to_boolean(value):
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def read_tests_csv_to_lists(file_path):
    with open(os.path.join(file_path, "test_results_original_ochiai.csv"), 'r') as csvfile:
        reader = csv.reader(csvfile)
        test_names = []
        test_results = []
        for row in reader:
            test_names.append(row[0].replace("\n", ""))  # First column
            test_results.append(convert_to_boolean(row[1]))
    return test_names, test_results


def get_unique_tests_that_cover_the_methods(stackTraceMethodsDetails, file_path):
    first_st_file = list(stackTraceMethodsDetails.keys())[0]
    first_st_method = list(stackTraceMethodsDetails[first_st_file].keys())[0]
    tests_covering_stack_traces_details = json_file_to_dict(file_path)
    repeated_test_methods = list(
        tests_covering_stack_traces_details[first_st_file][first_st_method]["tests_covering_the_method"].keys())
    for st_file in stackTraceMethodsDetails.keys():
        for st_method in stackTraceMethodsDetails[st_file].keys():
            removal_list = []
            for test in repeated_test_methods:
                if test not in tests_covering_stack_traces_details[st_file][st_method][
                    "tests_covering_the_method"].keys():
                    removal_list.append(test)
            for test in removal_list:
                repeated_test_methods.remove(test)

    result = {}
    for st_file in stackTraceMethodsDetails.keys():
        for st_method in stackTraceMethodsDetails[st_file].keys():
            unique_test_methods = list(
                tests_covering_stack_traces_details[st_file][st_method]["tests_covering_the_method"].keys())
            removal_list = []
            for test in unique_test_methods:
                if test in repeated_test_methods:
                    removal_list.append(test)
            for test in removal_list:
                unique_test_methods.remove(test)
            if st_file not in result.keys():
                result[st_file] = {}
            result[st_file][st_method] = unique_test_methods
    return result


def store_fake_test_results(coverage, project, bug_id, gzoltar_files_path, file_name):
    project_gzoltar_folder = os.path.join(gzoltar_files_path, project)
    bug_gzoltar_folder = os.path.join(project_gzoltar_folder, bug_id)
    test_names = coverage["test_names"]
    fake_test_results = coverage["fake_test_results"]
    fake_test_results_file_path = os.path.join(bug_gzoltar_folder, file_name)
    write_two_lists_to_csv(test_names, fake_test_results, fake_test_results_file_path)


def find_file_complete_name(file, bug_data):
    for file_complete_name in bug_data["stackTraceMethodsDetails"].keys():
        if file_complete_name.endswith(file):
            return file_complete_name
    return None


def get_top_n_keys(dictionary, keys_to_consider, n):
    sorted_dict = sorted(dictionary.items(), key=lambda x: x[1], reverse=True)
    filtered_dict = [(key, value) for key, value in sorted_dict if key in keys_to_consider]
    top_n_pairs = filtered_dict[:n]
    top_n_keys = [pair[0] for pair in top_n_pairs]
    return top_n_keys
