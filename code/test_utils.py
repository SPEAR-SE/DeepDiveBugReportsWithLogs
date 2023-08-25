import unittest
import os
import importlib
import utils
import json
import tempfile
import shutil

importlib.reload(utils)


class TestCountLinesOfCodeForCoverage(unittest.TestCase):

    def setUp(self):
        os.makedirs('test_project', exist_ok=True)

    def tearDown(self):
        for filename in os.listdir('test_project'):
            os.remove(os.path.join('test_project', filename))
        os.rmdir('test_project')

    def test_normal_case_all_covered(self):
        with open('test_project/test_file.java', 'w') as file:
            file.write("line1;\nline2;\nline3;\n")
        count = utils.count_lines_of_code_for_coverage('test_file.java', 'test_project', [1, 2, 3])
        self.assertEqual(count, 3)

    def test_normal_case_not_covered(self):
        with open('test_project/test_file.java', 'w') as file:
            file.write("""line1;\nline2;\nline3;\n""")
        count = utils.count_lines_of_code_for_coverage('test_file.java', 'test_project', [])
        self.assertEqual(count, 3)

    def test_with_begin_and_end_line(self):
        with open('test_project/test_file.java', 'w') as file:
            file.write("line1;\nline2;\nline3;\n")
        count = utils.count_lines_of_code_for_coverage('test_file.java', 'test_project', [], 1, 2)
        self.assertEqual(count, 2)

    def test_with_multiline_comments(self):
        with open('test_project/test_file_with_comments.java', 'w') as file:
            file.write("/*\nline1\n*/\nline2;\n")
        count = utils.count_lines_of_code_for_coverage('test_file_with_comments.java', 'test_project', [])
        self.assertEqual(count, 1)

    def test_empty_file(self):
        with open('test_project/empty_file.java', 'w') as file:
            file.write("")
        count = utils.count_lines_of_code_for_coverage('empty_file.java', 'test_project', [])
        self.assertEqual(count, 0)

    def test_non_existing_file(self):
        with self.assertRaises(FileNotFoundError):
            utils.count_lines_of_code_for_coverage('non_existent.java', 'test_project', [])

    def test_real_java_file(self):
        with open('test_project/real_java_file.java', 'w') as file:
            file.write("""public class Example {
    public static void main(
                     String[] args) { //Definition with line break
        // Single-line comment: This is the starting point of the program

        /* Multi-line comment:
           Initializing variables to demonstrate loops and conditions */
        int outerLimit = 5;
        int innerLimit = 3;

        // Loop to iterate from 0 to outerLimit
        for (int i = 0; i < outerLimit; i++) {
            System.out.println("Outer loop iteration: " + i);

            // If condition to check if 'i' is even
            if (i % 2 == 0) {
                System.out.println("This is an even iteration in the outer loop.");
            }

            /* Nested loop with an inner if:
               Iterating through the inner loop from 0 to innerLimit */
            j=0;
            while (j < innerLimit) {
                System.out.println("  Inner loop iteration: " + j);

                // If condition to check if 'j' is equal to 1
                if (j == 1) {
                    System.out.println("  This iteration in the inner loop has j equal to 1.");
                } else {
                     System.out.println("  This iteration in the inner loop has j different from 1.");
                }
                j = j+1;
            }
        }
    }
}

            """)
        count = utils.count_lines_of_code_for_coverage('real_java_file.java', 'test_project', [])
        self.assertEqual(count, 11)

    def test_real_java_file2(self):
        with open('test_project/real_java_file.java', 'w') as file:
            file.write("""public class ComplexExample {
        public static void main(String[] args) {
            int[] numbers = {10, 20, 30, 40, 50}; //Hey
    
            try {
                //hey2;
                for (int i = 0; i <= numbers.length; i++) {
                    if (i == numbers.length) {
                    /*hey3;*/
                        throw new ArrayIndexOutOfBoundsException("Index out of bounds");
                    }
                    if (numbers[i] % 20 == 0) {
                        System.out.println("Divisible by 20: " + numbers[i]);
                    } else {
                        /*
                        hey4;
                        */
                        System.out.println("Not divisible by 20: " + numbers[i]);
                    }
                }
            } catch (ArrayIndexOutOfBoundsException e) {
                System.err.println("Caught exception: " + e.getMessage());
            } finally {
                System.out.println("Execution completed, whether an exception was thrown or not.");
            }
        }
    
        public static void printMessage() {
            System.out.println("This is a complex Java example!");
        }
    }
    """)
        count = utils.count_lines_of_code_for_coverage('real_java_file.java', 'test_project', [])
        self.assertEqual(count, 8)


class TestGetMethodCoveredLinesList(unittest.TestCase):

    def test_within_range(self):
        buggy_file_covered_lines = [5, 10, 15, 20]
        start_line = 10
        end_line = 15
        expected = [10, 15]
        result = utils.get_method_covered_lines_list(buggy_file_covered_lines, start_line, end_line)
        self.assertEqual(result, expected)

    def test_outside_range(self):
        buggy_file_covered_lines = [5, 10, 15, 20]
        start_line = 16
        end_line = 18
        expected = []
        result = utils.get_method_covered_lines_list(buggy_file_covered_lines, start_line, end_line)
        self.assertEqual(result, expected)

    def test_include_all_lines(self):
        buggy_file_covered_lines = [5, 10, 15, 20]
        start_line = 0
        end_line = 20
        expected = [5, 10, 15, 20]
        result = utils.get_method_covered_lines_list(buggy_file_covered_lines, start_line, end_line)
        self.assertEqual(result, expected)

    def test_empty_input(self):
        buggy_file_covered_lines = []
        start_line = 5
        end_line = 20
        expected = []
        result = utils.get_method_covered_lines_list(buggy_file_covered_lines, start_line, end_line)
        self.assertEqual(result, expected)

    def test_invalid_range(self):
        buggy_file_covered_lines = [5, 10, 15, 20]
        start_line = 20
        end_line = 5
        expected = []
        result = utils.get_method_covered_lines_list(buggy_file_covered_lines, start_line, end_line)
        self.assertEqual(result, expected)


class TestSortDictFunction(unittest.TestCase):

    def test_basic_functionality(self):
        dictionary = {'a': 3, 'b': 1, 'c': 2}
        expected = {'a': 3, 'c': 2, 'b': 1}
        self.assertEqual(utils.sort_dict_by_values_reverse_order(dictionary), expected)

    def test_empty_dictionary(self):
        dictionary = {}
        expected = {}
        self.assertEqual(utils.sort_dict_by_values_reverse_order(dictionary), expected)

    def test_edge_cases_with_duplicate_values(self):
        dictionary = {'a': 3, 'b': 1, 'c': 2, 'd': 3}
        sorted_dict = utils.sort_dict_by_values_reverse_order(dictionary)
        self.assertEqual(sorted_dict['a'], 3)
        self.assertEqual(sorted_dict['d'], 3)
        self.assertTrue(list(sorted_dict.values()) == [3, 3, 2, 1])

    def test_non_integer_values(self):
        # Floating point values
        dictionary = {'a': 3.5, 'b': 1.2, 'c': 2.8}
        expected = {'a': 3.5, 'c': 2.8, 'b': 1.2}
        self.assertEqual(utils.sort_dict_by_values_reverse_order(dictionary), expected)

        # String values
        dictionary = {'a': 'apple', 'b': 'banana', 'c': 'cherry'}
        expected = {'c': 'cherry', 'b': 'banana', 'a': 'apple'}
        self.assertEqual(utils.sort_dict_by_values_reverse_order(dictionary), expected)

    def test_large_dictionary(self):
        dictionary = {str(i): i for i in range(1000)}
        expected = {str(999 - i): 999 - i for i in range(1000)}
        self.assertEqual(utils.sort_dict_by_values_reverse_order(dictionary), expected)


class TestFindMethodInRankingDataFunction(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {'methodA': 'dataA', 'methodB': 'dataB'}
        method = 'com.example.methodA'
        expected = 'methodA'
        self.assertEqual(utils.find_method_in_ranking_data(method, ranking_data), expected)

    def test_no_matching_method(self):
        ranking_data = {'methodA': 'dataA', 'methodB': 'dataB'}
        method = 'com.example.methodC'
        self.assertIsNone(utils.find_method_in_ranking_data(method, ranking_data))

    def test_multiple_possible_matches(self):
        ranking_data = {'methodA': 'dataA', 'com.example.methodA': 'dataB'}
        method = 'com.example.methodA'
        # As 'com.example.methodA' is the exact match and also the latter key,
        # it should be the one that is returned.
        expected = 'com.example.methodA'
        self.assertEqual(utils.find_method_in_ranking_data(method, ranking_data), expected)

    def test_empty_ranking_data(self):
        ranking_data = {}
        method = 'com.example.methodA'
        self.assertIsNone(utils.find_method_in_ranking_data(method, ranking_data))


class TestGetNumberOfBuggyMethodsInTopN(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {'methodA': 1, 'methodB': 2, 'methodC': 3}
        buggy_methods_list = ['com.example.methodA', 'com.example.methodB']
        result = utils.get_number_of_buggy_methods_in_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 2)

    def test_no_buggy_methods_in_top_n(self):
        ranking_data = {'methodA': 1, 'methodB': 2, 'methodC': 3}
        buggy_methods_list = ['com.example.methodC']
        result = utils.get_number_of_buggy_methods_in_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 0)

    def test_exception_scenario(self):
        ranking_data = {'methodA': 1}
        buggy_methods_list = ['com.example.methodX']  # methodX does not exist in ranking_data
        result = utils.get_number_of_buggy_methods_in_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 0)

    def test_larger_n_than_ranking_data(self):
        ranking_data = {'methodA': 1, 'methodB': 2}
        buggy_methods_list = ['com.example.methodA', 'com.example.methodB', 'com.example.methodC']
        result = utils.get_number_of_buggy_methods_in_top_n(ranking_data, 5, buggy_methods_list)
        self.assertEqual(result, 2)

    def test_multiple_buggy_methods_same_rank(self):
        ranking_data = {'methodA': 1, 'methodB': 1, 'methodC': 2}
        buggy_methods_list = ['com.example.methodA', 'com.example.methodB']
        result = utils.get_number_of_buggy_methods_in_top_n(ranking_data, 1, buggy_methods_list)
        self.assertEqual(result, 2)


class TestGetFirstBuggyMethodInStackTrace(unittest.TestCase):

    def test_basic_functionality(self):
        buggy_methods = ['com.example.ClassA#methodA']
        stack_trace = ['com.example.ClassA.methodA', 'com.example.ClassB.methodB']
        result = utils.get_first_buggy_method_in_stack_trace(buggy_methods, stack_trace)
        self.assertEqual(result, 1)

    def test_no_buggy_method_in_stack_trace(self):
        buggy_methods = ['com.example.ClassC#methodC']
        stack_trace = ['com.example.ClassA.methodA', 'com.example.ClassB.methodB']
        result = utils.get_first_buggy_method_in_stack_trace(buggy_methods, stack_trace)
        self.assertEqual(result, "not found")

    def test_multiple_buggy_methods(self):
        buggy_methods = ['com.example.ClassA#methodA', 'com.example.ClassB#methodB']
        stack_trace = ['com.example.ClassB.methodB', 'com.example.ClassA.methodA']
        result = utils.get_first_buggy_method_in_stack_trace(buggy_methods, stack_trace)
        self.assertEqual(result, 1)

    def test_method_format_adjustment(self):
        buggy_methods = ['com.example.ClassA#methodA']
        stack_trace = ['com.example.ClassA#methodA']
        result = utils.get_first_buggy_method_in_stack_trace(buggy_methods, stack_trace)
        self.assertEqual(result, 1)

    def test_empty_inputs(self):
        buggy_methods = []
        stack_trace = []
        result = utils.get_first_buggy_method_in_stack_trace(buggy_methods, stack_trace)
        self.assertEqual(result, "not found")


class TestGetBestClassifiedBuggyMethod(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {'com.example.ClassA#methodA': 1, 'com.example.ClassB#methodB': 2}
        buggy_methods = ['com.example.ClassA#methodA']
        result = utils.get_best_classified_buggy_method(ranking_data, buggy_methods)
        self.assertEqual(result, 1)

    def test_no_buggy_method_in_ranking_data(self):
        ranking_data = {'com.example.ClassA#methodA': 1, 'com.example.ClassB#methodB': 2}
        buggy_methods = ['com.example.ClassC#methodC']
        result = utils.get_best_classified_buggy_method(ranking_data, buggy_methods)
        self.assertEqual(result, "not found")

    def test_multiple_buggy_methods(self):
        ranking_data = {'com.example.ClassA#methodA': 3, 'com.example.ClassB#methodB': 2,
                        'com.example.ClassC#methodC': 1}
        buggy_methods = ['com.example.ClassA#methodA', 'com.example.ClassB#methodB']
        result = utils.get_best_classified_buggy_method(ranking_data, buggy_methods)
        self.assertEqual(result, 2)

    def test_empty_inputs(self):
        ranking_data = {}
        buggy_methods = []
        result = utils.get_best_classified_buggy_method(ranking_data, buggy_methods)
        self.assertEqual(result, "not found")

    def test_some_buggy_methods_not_in_ranking_data(self):
        ranking_data = {'com.example.ClassA#methodA': 2}
        buggy_methods = ['com.example.ClassA#methodA', 'com.example.ClassC#methodC']
        result = utils.get_best_classified_buggy_method(ranking_data, buggy_methods)
        self.assertEqual(result, 2)


class TestGetPrecisionTopN(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {'com.example.ClassA#methodA': 1, 'com.example.ClassB#methodB': 2}
        buggy_methods = ['com.example.ClassA#methodA']
        result = utils.get_precision_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0.5)

    def test_no_buggy_method_in_top_n(self):
        ranking_data = {'com.example.ClassA#methodA': 3, 'com.example.ClassB#methodB': 2,
                        'com.example.ClassC#methodC': 1}
        buggy_methods = ['com.example.ClassA#methodA']
        result = utils.get_precision_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0)

    def test_all_top_n_are_buggy_methods(self):
        ranking_data = {'com.example.ClassA#methodA': 1, 'com.example.ClassB#methodB': 2}
        buggy_methods = ['com.example.ClassA#methodA', 'com.example.ClassB#methodB']
        result = utils.get_precision_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 1)

    def test_some_buggy_methods_in_top_n(self):
        ranking_data = {'com.example.ClassA#methodA': 3, 'com.example.ClassB#methodB': 1,
                        'com.example.ClassC#methodC': 2}
        buggy_methods = ['com.example.ClassA#methodA', 'com.example.ClassC#methodC']
        result = utils.get_precision_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0.5)

    def test_empty_inputs(self):
        ranking_data = {}
        buggy_methods = []
        result = utils.get_precision_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0)

    def test_n_larger_than_ranking_data(self):
        ranking_data = {'com.example.ClassA#methodA': 1}
        buggy_methods = ['com.example.ClassA#methodA']
        result = utils.get_precision_top_n(ranking_data, 3, buggy_methods)
        self.assertEqual(result, 1 / 3)


class TestExtractBuggyMethodsList(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {'com.example.ClassA#methodA': 1}
        buggy_methods_data = {'com.example.ClassA.java': ['methodA']}
        result = utils.extract_buggy_methods_list(ranking_data, buggy_methods_data)
        self.assertEqual(result, ['com.example.ClassA#methodA'])

    def test_method_not_found_in_ranking_data(self):
        ranking_data = {}
        buggy_methods_data = {'ClassA.java': ['methodA']}
        result = utils.extract_buggy_methods_list(ranking_data, buggy_methods_data)
        self.assertEqual(result, ['ClassA#methodA'])

    def test_method_with_different_name_in_ranking_data(self):
        ranking_data = {'com.example.ClassA#methodA': 1}
        buggy_methods_data = {'com/example/ClassA.java': ['methodA']}
        result = utils.extract_buggy_methods_list(ranking_data, buggy_methods_data)
        self.assertEqual(result, ['com.example.ClassA#methodA'])

    def test_empty_inputs(self):
        ranking_data = {}
        buggy_methods_data = {}
        result = utils.extract_buggy_methods_list(ranking_data, buggy_methods_data)
        self.assertEqual(result, [])


class TestGetRecallTopN(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {
            'methodA': 5,
            'methodB': 4,
            'methodC': 3,
            'methodD': 2,
            'methodE': 1
        }
        buggy_methods_list = ['methodA', 'methodD']

        result = utils.get_recall_top_n(ranking_data, 3, buggy_methods_list)
        self.assertEqual(result, 0.5)  # Only methodD is in top 3, so recall is 0.5

    def test_empty_buggy_methods(self):
        ranking_data = {'methodA': 1, 'methodB': 2}
        buggy_methods_list = []

        result = utils.get_recall_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 0)  # No buggy methods to consider

    def test_empty_ranking_data(self):
        ranking_data = {}
        buggy_methods_list = ['methodA', 'methodB']

        result = utils.get_recall_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 0)  # No methods in the ranking data

    def test_all_buggy_methods_in_top_n(self):
        ranking_data = {
            'methodA': 1,
            'methodB': 2,
            'methodC': 3,
            'methodD': 4
        }
        buggy_methods_list = ['methodA', 'methodB']

        result = utils.get_recall_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 1.0)  # All buggy methods are in top 2

    def test_no_buggy_methods_in_top_n(self):
        ranking_data = {
            'methodA': 3,
            'methodB': 4,
            'methodC': 1,
            'methodD': 2
        }
        buggy_methods_list = ['methodA', 'methodB']

        result = utils.get_recall_top_n(ranking_data, 2, buggy_methods_list)
        self.assertEqual(result, 0)  # No buggy methods are in top 2


class TestGetF1TopN(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_data = {
            'methodA': 5,
            'methodB': 4,
            'methodC': 3,
            'methodD': 2,
            'methodE': 1
        }
        buggy_methods = ['methodA', 'methodD']

        result = utils.get_f1_top_n(ranking_data, 3, buggy_methods)
        expected_f1 = 2 * (1 / 3 * 0.5) / (1 / 3 + 0.5)  # Using the known precision and recall values
        self.assertEqual(result, expected_f1)

    def test_no_buggy_methods_in_top_n(self):
        ranking_data = {
            'methodA': 5,
            'methodB': 4,
            'methodC': 3,
            'methodD': 2,
            'methodE': 1
        }
        buggy_methods = ['methodF', 'methodG']

        result = utils.get_f1_top_n(ranking_data, 3, buggy_methods)
        self.assertEqual(result, 0)

    def test_all_buggy_methods_in_top_n(self):
        ranking_data = {
            'methodA': 1,
            'methodB': 2
        }
        buggy_methods = ['methodA', 'methodB']

        result = utils.get_f1_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 1.0)  # Precision and recall are both 1

    def test_empty_buggy_methods(self):
        ranking_data = {'methodA': 1, 'methodB': 2}
        buggy_methods = []

        result = utils.get_f1_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0)  # No buggy methods to consider

    def test_empty_ranking_data(self):
        ranking_data = {}
        buggy_methods = ['methodA', 'methodB']

        result = utils.get_f1_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0)  # No methods in the ranking data

    def test_recall_zero_precision_zero(self):
        ranking_data = {
            'methodA': 4,
            'methodB': 3,
            'methodC': 2,
            'methodD': 1
        }
        buggy_methods = ['methodE']

        result = utils.get_f1_top_n(ranking_data, 2, buggy_methods)
        self.assertEqual(result, 0)


class TestGetMethodRankFunction(unittest.TestCase):

    def test_basic_functionality(self):
        ranking_info = {
            'com.example.methodA': 1,
            'com.example.methodB': 2,
            'com.example.methodC': 3
        }
        method = 'com.example.methodB'
        result = utils.get_method_rank(ranking_info, method)
        self.assertEqual(result, 2)

    def test_method_not_in_ranking(self):
        ranking_info = {
            'com.example.methodA': 1,
            'com.example.methodB': 2
        }
        method = 'com.example.methodZ'
        result = utils.get_method_rank(ranking_info, method)
        self.assertEqual(result, float('inf'))

    def test_multiple_possible_matches(self):
        ranking_info = {
            'com.example.methodA': 1,
            'example.methodA': 2
        }
        method = 'example.methodA'
        result = utils.get_method_rank(ranking_info, method)
        self.assertEqual(result, 2)


class TestGetStRakingDictFunction(unittest.TestCase):

    def test_basic_functionality(self):
        stack_trace_methods = [
            'com.example.ClassA.methodA',
            'com.example.ClassB.methodB',
            'com.example.ClassC.methodC'
        ]
        expected = {
            'com.example.ClassA#methodA': 1,
            'com.example.ClassB#methodB': 2,
            'com.example.ClassC#methodC': 3
        }
        result = utils.get_st_raking_dict(stack_trace_methods)
        self.assertEqual(result, expected)

    def test_special_characters_in_method_name(self):
        stack_trace_methods = ['com.example.ClassA.methodA$', 'com.example.ClassB.methodB?']
        expected = {
            'com.example.ClassA#methodA$': 1,
            'com.example.ClassB#methodB?': 2
        }
        result = utils.get_st_raking_dict(stack_trace_methods)
        self.assertEqual(result, expected)

    def test_no_dot_in_method_name(self):
        stack_trace_methods = ['methodA', 'methodB']
        expected = {}
        result = utils.get_st_raking_dict(stack_trace_methods)
        self.assertEqual(result, expected)

    def test_empty_stack_trace(self):
        stack_trace_methods = []
        expected = {}
        result = utils.get_st_raking_dict(stack_trace_methods)
        self.assertEqual(result, expected)


class TestGetMRRFunction(unittest.TestCase):
    ranking_files_path = "/tmp"  # Adjust as needed.

    project_bugs_data = {
        "bug_001": {
            "buggyMethods": {
                "src/java/org/apache/commons/cli2/option/GroupImpl.java": {
                    "validate": {
                        "endLine": "285",
                        "bugReportCommitEndLine": "285",
                        "startLine": "237",
                        "bugReportCommitStartLine": "237"
                    }
                }
            },
            "stack_trace_methods": [
                "org.apache.commons.cli2.validation.FileValidator.validate",
                "org.apache.commons.cli2.option.ArgumentImpl.validate",
                "org.apache.commons.cli2.option.ParentImpl.validate",
                "org.apache.commons.cli2.option.DefaultOption.validate",
                "org.apache.commons.cli2.option.GroupImpl.validate",
                "org.apache.commons.cli2.commandline.Parser.parse",
                "org.apache.commons.cli2.commandline.Parser.parseAndHelp",
                "org.apache.commons.cli2.issues.CLI2Sample.main"
            ]
        }
    }

    @classmethod
    def setUpClass(cls):
        original_ochiai_ranking = {
            "src.java.org.apache.commons.cli2.option.GroupImpl#validate": 1,
            "SomeOtherMethod.method": 2,
            "src.java.org.apache.commons.cli2.commandline.Parser#parse": 3,
            "src.java.org.apache.commons.cli2.validation.FileValidator#validate": 4
        }

        project_dir = os.path.join(cls.ranking_files_path, "originalOchiai", "ProjectA")
        os.makedirs(project_dir, exist_ok=True)

        with open(os.path.join(project_dir, "bug_001.json"), "w") as f:
            json.dump(original_ochiai_ranking, f)

    @classmethod
    def tearDownClass(cls):
        # Cleaning up the test data.
        os.remove(os.path.join(cls.ranking_files_path, "originalOchiai", "ProjectA", "bug_001.json"))

    def test_with_stack_traces_mrr(self):
        result = utils.get_mrr("ProjectA", "stackTraces", self.project_bugs_data, self.ranking_files_path)
        self.assertEqual(result, 0.2)

    def test_with_originalOchiai_mrr(self):
        result = utils.get_mrr("ProjectA", "originalOchiai", self.project_bugs_data, self.ranking_files_path)
        self.assertEqual(result, 1)

    def test_multiple_bugs_diverse_methods_mrr_ochiai(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassOne.methodOne"
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassTwo.methodTwo",
                    "some.package.ClassTwo.methodThree"
                ]
            }
        }

        # Mocking the ranking file data for the original Ochiai
        original_ochiai_ranking_1 = {
            "src.java.some.package.ClassOne#methodOne": 5,
            "src.java.some.package.ClassTwo#methodTwo": 2,
            "SomeOtherMethod.method": 1,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
        }
        original_ochiai_ranking_2 = {
            "src.java.some.package.ClassOne#methodOne": 1,
            "src.java.some.package.ClassTwo#methodTwo": 10,
            "SomeOtherMethod.method": 4,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
            "SomeOtherMethod.method8": 5,
            "SomeOtherMethod.method4": 7,
            "SomeOtherMethod.method5": 7,
            "SomeOtherMethod.method6": 8,
            "SomeOtherMethod.method7": 9,
        }

        # Saving the mocked ranking to a file
        ranking_file_path = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_001.json")
        os.makedirs(os.path.dirname(ranking_file_path), exist_ok=True)
        with open(ranking_file_path, 'w') as f:
            json.dump(original_ochiai_ranking_1, f)

        ranking_file_path_bug_002 = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_002.json")
        with open(ranking_file_path_bug_002, 'w') as f:
            json.dump(original_ochiai_ranking_2, f)
        result = utils.get_mrr(self.project, "originalOchiai", project_bugs_data, self.test_dir)
        self.assertAlmostEqual(result, 0.15, places=2)

        # Clean up
        shutil.rmtree(self.test_dir)

    def test_multiple_bugs_diverse_methods_mrr_ochiai_2(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassOne.methodOne"
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassTwo.methodTwo",
                    "some.package.ClassTwo.methodThree"
                ]
            }
        }

        # Mocking the ranking file data for the original Ochiai
        original_ochiai_ranking_1 = {
            "src.java.some.package.ClassOne#methodOne": 2,
            "src.java.some.package.ClassTwo#methodTwo": 2,
            "SomeOtherMethod.method": 5,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
        }
        original_ochiai_ranking_2 = {
            "src.java.some.package.ClassOne#methodOne": 1,
            "src.java.some.package.ClassTwo#methodTwo": 8,
            "src.java.some.package.ClassTwo#methodThree": 2,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
            "SomeOtherMethod.method8": 5,
            "SomeOtherMethod.method4": 7,
            "SomeOtherMethod.method5": 7,
            "SomeOtherMethod.method6": 10,
            "SomeOtherMethod.method7": 9,
        }

        # Saving the mocked ranking to a file
        ranking_file_path = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_001.json")
        os.makedirs(os.path.dirname(ranking_file_path), exist_ok=True)
        with open(ranking_file_path, 'w') as f:
            json.dump(original_ochiai_ranking_1, f)

        ranking_file_path_bug_002 = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_002.json")
        with open(ranking_file_path_bug_002, 'w') as f:
            json.dump(original_ochiai_ranking_2, f)
        result = utils.get_mrr(self.project, "originalOchiai", project_bugs_data, self.test_dir)
        self.assertAlmostEqual(result, 0.5, places=2)

        # Clean up
        shutil.rmtree(self.test_dir)

    def test_multiple_bugs_diverse_methods_mrr_st(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "SomeOtherMethod.method",
                    "src.java.some.package.ClassTwo.methodTwo",
                    "SomeOtherMethod.method3",
                    "SomeOtherMethod.method2",
                    "src.java.some.package.ClassOne.methodOne"
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "src.java.some.package.ClassOne.methodOne",
                    "SomeOtherMethod.method",
                    "SomeOtherMethod.method2",
                    "SomeOtherMethod.method3",
                    "SomeOtherMethod.method8",
                    "SomeOtherMethod.method4",
                    "SomeOtherMethod.method5",
                    "SomeOtherMethod.method6",
                    "SomeOtherMethod.method7",
                    "src.java.some.package.ClassTwo.methodTwo"
                ]
            }
        }

        result = utils.get_mrr(self.project, "stackTraces", project_bugs_data, None)
        self.assertAlmostEqual(result, 0.15, places=2)

    def test_multiple_bugs_diverse_methods_mrr_st_2(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "SomeOtherMethod.method",
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "src.java.some.package.ClassOne.methodOne",
                    "SomeOtherMethod.method",
                    "SomeOtherMethod.method2",
                    "SomeOtherMethod.method3",
                    "SomeOtherMethod.method8",
                    "SomeOtherMethod.method4",
                    "SomeOtherMethod.method5",
                    "SomeOtherMethod.method6",
                    "SomeOtherMethod.method7",
                    "src.java.some.package.ClassTwo.methodTwo"
                ]
            }
        }

        result = utils.get_mrr(self.project, "stackTraces", project_bugs_data, None)
        self.assertAlmostEqual(result, 0.05, places=2)


class TestGetMAPFunction(unittest.TestCase):
    ranking_files_path = "/tmp"  # Adjust as needed.

    project_bugs_data = {
        "bug_001": {
            "buggyMethods": {
                "src/java/org/apache/commons/cli2/option/GroupImpl.java": {
                    "validate": {
                        "endLine": "285",
                        "bugReportCommitEndLine": "285",
                        "startLine": "237",
                        "bugReportCommitStartLine": "237"
                    }
                }
            },
            "stack_trace_methods": [
                "org.apache.commons.cli2.validation.FileValidator.validate",
                "org.apache.commons.cli2.option.ArgumentImpl.validate",
                "org.apache.commons.cli2.option.ParentImpl.validate",
                "org.apache.commons.cli2.option.DefaultOption.validate",
                "org.apache.commons.cli2.option.GroupImpl.validate",
                "org.apache.commons.cli2.commandline.Parser.parse",
                "org.apache.commons.cli2.commandline.Parser.parseAndHelp",
                "org.apache.commons.cli2.issues.CLI2Sample.main"
            ]
        }
    }

    @classmethod
    def setUpClass(cls):
        original_ochiai_ranking = {
            "src.java.org.apache.commons.cli2.option.GroupImpl#validate": 1,
            "SomeOtherMethod.method": 2,
            "src.java.org.apache.commons.cli2.commandline.Parser#parse": 3,
            "src.java.org.apache.commons.cli2.validation.FileValidator#validate": 4
        }

        project_dir = os.path.join(cls.ranking_files_path, "originalOchiai", "ProjectA")
        os.makedirs(project_dir, exist_ok=True)

        with open(os.path.join(project_dir, "bug_001.json"), "w") as f:
            json.dump(original_ochiai_ranking, f)

    @classmethod
    def tearDownClass(cls):
        # Cleaning up the test data.
        os.remove(os.path.join(cls.ranking_files_path, "originalOchiai", "ProjectA", "bug_001.json"))

    def test_with_stack_traces_map(self):
        result = utils.get_map("ProjectA", "stackTraces", self.project_bugs_data, self.ranking_files_path)
        self.assertEqual(result, 0.2)

    def test_with_originalOchiai_map(self):
        result = utils.get_map("ProjectA", "originalOchiai", self.project_bugs_data, self.ranking_files_path)
        self.assertEqual(result, 1)

    def test_multiple_bugs_diverse_methods_map_ochiai(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassOne.methodOne"
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassTwo.methodTwo",
                    "some.package.ClassTwo.methodThree"
                ]
            }
        }

        # Mocking the ranking file data for the original Ochiai
        original_ochiai_ranking_1 = {
            "src.java.some.package.ClassOne#methodOne": 5,
            "src.java.some.package.ClassTwo#methodTwo": 2,
            "SomeOtherMethod.method": 1,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
        }
        original_ochiai_ranking_2 = {
            "src.java.some.package.ClassOne#methodOne": 1,
            "src.java.some.package.ClassTwo#methodTwo": 10,
            "SomeOtherMethod.method": 4,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
            "SomeOtherMethod.method8": 5,
            "SomeOtherMethod.method4": 7,
            "SomeOtherMethod.method5": 7,
            "SomeOtherMethod.method6": 8,
            "SomeOtherMethod.method7": 9,
        }

        # Saving the mocked ranking to a file
        ranking_file_path = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_001.json")
        os.makedirs(os.path.dirname(ranking_file_path), exist_ok=True)
        with open(ranking_file_path, 'w') as f:
            json.dump(original_ochiai_ranking_1, f)

        ranking_file_path_bug_002 = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_002.json")
        with open(ranking_file_path_bug_002, 'w') as f:
            json.dump(original_ochiai_ranking_2, f)
        result = utils.get_map(self.project, "originalOchiai", project_bugs_data, self.test_dir)
        self.assertAlmostEqual(result, 0.125, places=2)

        # Clean up
        shutil.rmtree(self.test_dir)

    def test_multiple_bugs_diverse_methods_map_ochiai_2(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassOne.methodOne"
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "some.package.ClassTwo.methodTwo",
                    "some.package.ClassTwo.methodThree"
                ]
            }
        }

        # Mocking the ranking file data for the original Ochiai
        original_ochiai_ranking_1 = {
            "src.java.some.package.ClassOne#methodOne": 2,
            "src.java.some.package.ClassTwo#methodTwo": 2,
            "SomeOtherMethod.method": 5,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
        }
        original_ochiai_ranking_2 = {
            "src.java.some.package.ClassOne#methodOne": 1,
            "src.java.some.package.ClassTwo#methodTwo": 8,
            "src.java.some.package.ClassTwo#methodThree": 2,
            "SomeOtherMethod.method2": 4,
            "SomeOtherMethod.method3": 4,
            "SomeOtherMethod.method8": 5,
            "SomeOtherMethod.method4": 7,
            "SomeOtherMethod.method5": 7,
            "SomeOtherMethod.method6": 10,
            "SomeOtherMethod.method7": 9,
        }

        # Saving the mocked ranking to a file
        ranking_file_path = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_001.json")
        os.makedirs(os.path.dirname(ranking_file_path), exist_ok=True)
        with open(ranking_file_path, 'w') as f:
            json.dump(original_ochiai_ranking_1, f)

        ranking_file_path_bug_002 = os.path.join(self.test_dir, "originalOchiai", self.project, "bug_002.json")
        with open(ranking_file_path_bug_002, 'w') as f:
            json.dump(original_ochiai_ranking_2, f)
        result = utils.get_map(self.project, "originalOchiai", project_bugs_data, self.test_dir)
        self.assertAlmostEqual(result, 0.4375, places=2)

        # Clean up
        shutil.rmtree(self.test_dir)

    def test_multiple_bugs_diverse_methods_map_st(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "SomeOtherMethod.method",
                    "src.java.some.package.ClassTwo.methodTwo",
                    "SomeOtherMethod.method3",
                    "SomeOtherMethod.method2",
                    "src.java.some.package.ClassOne.methodOne"
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "src.java.some.package.ClassOne.methodOne",
                    "SomeOtherMethod.method",
                    "SomeOtherMethod.method2",
                    "SomeOtherMethod.method3",
                    "SomeOtherMethod.method8",
                    "SomeOtherMethod.method4",
                    "SomeOtherMethod.method5",
                    "SomeOtherMethod.method6",
                    "SomeOtherMethod.method7",
                    "src.java.some.package.ClassTwo.methodTwo"
                ]
            }
        }

        result = utils.get_map(self.project, "stackTraces", project_bugs_data, None)
        self.assertAlmostEqual(result, 0.125, places=2)

    def test_multiple_bugs_diverse_methods_map_st_2(self):
        # Create a temporary directory for the test
        self.test_dir = tempfile.mkdtemp()
        self.project = "ProjectA"

        # Mocking the project_bugs_data
        project_bugs_data = {
            "bug_001": {
                "buggyMethods": {
                    "src/java/some/package/ClassOne.java": {
                        "methodOne": {"startLine": "10", "endLine": "20"}
                    }
                },
                "stack_trace_methods": [
                    "SomeOtherMethod.method",
                ]
            },
            "bug_002": {
                "buggyMethods": {
                    "src/java/some/package/ClassTwo.java": {
                        "methodTwo": {"startLine": "10", "endLine": "20"},
                        "methodThree": {"startLine": "25", "endLine": "35"}
                    }
                },
                "stack_trace_methods": [
                    "src.java.some.package.ClassOne.methodOne",
                    "SomeOtherMethod.method",
                    "SomeOtherMethod.method2",
                    "SomeOtherMethod.method3",
                    "SomeOtherMethod.method8",
                    "SomeOtherMethod.method4",
                    "SomeOtherMethod.method5",
                    "SomeOtherMethod.method6",
                    "SomeOtherMethod.method7",
                    "src.java.some.package.ClassTwo.methodTwo"
                ]
            }
        }

        result = utils.get_map(self.project, "stackTraces", project_bugs_data, None)
        self.assertAlmostEqual(result, 0.025, places=2)


class TestRankMethods(unittest.TestCase):

    def test_all_the_same(self):
        ochiai_scores_all_the_same = {
            "method1": 0.9,
            "method2": 0.9,
            "method3": 0.9,
            "method4": 0.9,
            "method5": 0.9,
        }
        expected_ranking_all_the_same = {
            "method1": 5,
            "method2": 5,
            "method3": 5,
            "method4": 5,
            "method5": 5,
        }
        ranking = utils.rank_methods(ochiai_scores_all_the_same)
        self.assertEqual(ranking, expected_ranking_all_the_same)

    def test_all_the_same2(self):
        ochiai_scores_all_the_same2 = {
            "method1": 0,
            "method2": 0.0,
            "method3": 0,
            "method4": 0.0,
            "method5": 0,
        }
        expected_ranking_all_the_same2 = {
            "method1": 5,
            "method2": 5,
            "method3": 5,
            "method4": 5,
            "method5": 5,
        }
        ranking = utils.rank_methods(ochiai_scores_all_the_same2)
        self.assertEqual(ranking, expected_ranking_all_the_same2)

    def test_some_equal(self):
        ochiai_scores_some_equal = {
            "method1": 0.9,
            "method2": 0.8,
            "method3": 0.8,
            "method4": 0.7,
            "method5": 0.9,
        }
        expected_ranking_some_equal = {
            "method1": 2,
            "method2": 4,
            "method3": 4,
            "method4": 5,
            "method5": 2,
        }
        ranking = utils.rank_methods(ochiai_scores_some_equal)
        self.assertEqual(ranking, expected_ranking_some_equal)

    def test_all_different(self):
        ochiai_scores_all_different = {
            "method1": 1,
            "method2": 0,
            "method3": 0.1,
            "method4": 0.7,
            "method5": 0.952,
        }
        expected_all_different = {
            "method1": 1,
            "method2": 5,
            "method3": 4,
            "method4": 3,
            "method5": 2,
        }
        ranking = utils.rank_methods(ochiai_scores_all_different)
        self.assertEqual(ranking, expected_all_different)

    def test_empty(self):
        ochiai_scores_empty = {
        }
        expected_empty = {
        }
        ranking = utils.rank_methods(ochiai_scores_empty)
        self.assertEqual(ranking, expected_empty)

    def test_single_method(self):
        ochiai_scores_single_method = {
            "method1": 0.9,
        }
        expected_single_method = {
            "method1": 1,
        }
        ranking = utils.rank_methods(ochiai_scores_single_method)
        self.assertEqual(ranking, expected_single_method)

    def test_alternating_rankings(self):
        ochiai_scores_alternating = {
            "method1": 0.9,
            "method2": 0.7,
            "method3": 0.8,
            "method4": 0.6,
            "method5": 0.5,
        }
        expected_alternating = {
            "method1": 1,
            "method2": 3,
            "method3": 2,
            "method4": 4,
            "method5": 5,
        }
        ranking = utils.rank_methods(ochiai_scores_alternating)
        self.assertEqual(ranking, expected_alternating)

    def test_consecutive_equal_rankings(self):
        ochiai_scores_consecutive_equal = {
            "method1": 0.9,
            "method2": 0.9,
            "method3": 0.8,
            "method4": 0.8,
            "method5": 0.7,
        }
        expected_consecutive_equal = {
            "method1": 2,
            "method2": 2,
            "method3": 4,
            "method4": 4,
            "method5": 5,
        }
        ranking = utils.rank_methods(ochiai_scores_consecutive_equal)
        self.assertEqual(ranking, expected_consecutive_equal)

    def test_negative_scores(self):
        ochiai_scores_negative = {
            "method1": -0.9,
            "method2": 0.9,
            "method3": 0,
            "method4": -0.5,
            "method5": 0.5,
        }
        expected_negative = {
            "method1": 5,
            "method2": 1,
            "method3": 3,
            "method4": 4,
            "method5": 2,
        }
        ranking = utils.rank_methods(ochiai_scores_negative)
        self.assertEqual(ranking, expected_negative)


if __name__ == "__main__":
    unittest.main()

# %%
