#!/usr/bin/env python
"""
Test speedy_antlr_tool against grammars in antlr/grammars-v4
"""

import os
import sys
import time
import unittest
import threading
from pathlib import Path
import speedy_antlr_tool.package

MY_DIR = os.path.dirname(os.path.realpath(__file__))
GRAMMARS_DIR = os.path.join(MY_DIR, 'antlr-grammars-v4')
PARSERS_DIR = os.path.join(MY_DIR, 'generated')

class AntlrGrammarsV4Test(unittest.TestCase):
    """
    Parse test
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @staticmethod
    def find_package_dir(base_dir):
        'Find the setup.py build directory or base python src as fallback'
        # Try cpp extension build
        start_path = Path(base_dir)
        hits = list(start_path.glob('**/build/lib.*'))
        if len(hits) > 1:
            # Only allow one build target
            return ''
        elif len(hits) == 1:
            return hits[0]
        else:
            return os.path.join(base_dir, 'src')

    def test_abb_example(self):
        grammar_dir = self.find_package_dir(os.path.join(PARSERS_DIR, 'abb'))
        self.assertNotEqual(grammar_dir, '', msg='Could not find unique package directory')
        grammar_name = 'abb'
        example_file = os.path.join(GRAMMARS_DIR, 'abb', 'examples', 'robdata.sys')
        rule = 'module'
        sys.path.insert(0, str(grammar_dir))
        self.assertTrue(speedy_antlr_tool.package.test_grammar(grammar_name, example_file, rule))


if __name__ == "__main__":
    unittest.main()
