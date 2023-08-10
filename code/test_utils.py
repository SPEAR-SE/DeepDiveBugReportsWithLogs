import unittest
import os
import importlib
import utils

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
    self.assertEqual(count, 9)


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


if __name__ == "__main__":
    unittest.main()

# %%
