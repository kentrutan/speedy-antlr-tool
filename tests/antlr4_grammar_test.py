#!/usr/bin/env python
"""
Test against antlr4 grammars repository on GitHub
"""
import os
import unittest

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
GENERATED_DIR = os.path.join(FILE_DIR, 'generated')

def generate_parser(self, grammar_name, entry_rule, antlr_jar_file=None, keep_files=False):
    """Generate parsers
        0. Create folder named {{grammar_name_lower}} (rm -r if it already exists)
        0. Copy files from template into generated folder
        1. Substitute {{template_variables}}: antlr_jar_file, grammar_name, grammar_name_lower, entry_rule
        2. Run setup build
        3. Run tests
        4. Report results of tests to unittest
        5. Delete folder (if keep_files == False)

    """
    return exitval


def test_grammar(self, grammar_name):
    'Test given grammar'

    # TODO: How to unload previous test import?
    import test

    test.print_tree("input_file.txt")
    test.benchmark("input_file.txt", 1000)
    #TODO: compare parse tree?
    # with self.assertRaises(SystemExit) as context:
    #     self.run_compiler(args, check_errors=False)
    # self.assertEqual(context.exception.code, 0)

class AntlrGrammarsTest(unittest.TestCase):
    """Compare Python and C++ target results on ANTLR4 grammars
    """




if __name__ == '__main__':
    unittest.main()
