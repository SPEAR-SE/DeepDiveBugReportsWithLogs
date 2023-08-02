import unittest
import importlib
import utils
importlib.reload(utils)


class TestUtils(unittest.TestCase):

    def test_stack_traces_info_extraction(self):
        st_entry = "at com.fasterxml.jackson.databind.DeserializationContext.reportMappingException(" \
                   "DeserializationContext.java:1234)"
        file_name, method_name, file_line = utils.extract_file_method_and_line_from_a_stack_trace_entry(st_entry)
        self.assertEqual(file_name, "DeserializationContext.java")
        self.assertEqual(file_line, 1234)
        self.assertEqual(method_name, "com.fasterxml.jackson.databind.DeserializationContext.reportMappingException")


if __name__ == "__main__":
    unittest.main()
