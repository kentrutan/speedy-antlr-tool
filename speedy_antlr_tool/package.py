#!/usr/bin/env python
"""Tool to generate a package with both pure Python and Python with C++ extension parsers
"""
from lib2to3.pgen2 import grammar
import re
import os
import sys
import shutil
import argparse
import logging
import subprocess
from pathlib import Path
from typing import List, Tuple, Union, Optional

import jinja2 as jj

import speedy_antlr_tool

my_name = os.path.basename(__file__)
_DEBUG = True

log = logging.getLogger(my_name)
logging.basicConfig(stream=sys.stderr)

def snake_case(string: str):
    """Change given camel case string to snake case, leaving input snake case alone

    Examples:
    >>> snake_case('leadingLowerCase')
    'leading_lower_case'
    >>> snake_case('LeadingUpperCase')
    'leading_upper_case'
    >>> snake_case('LEADINGallCaps')
    'leadingall_caps'
    >>> snake_case('LEADINGAllCaps')
    'leadingall_caps'
    >>> snake_case('numberA01A')
    'number_a01a'
    >>> snake_case('snake_case_already')
    'snake_case_already'
    """
    return re.sub('([a-z])([A-Z0-9]+)', r'\1_\2', string).lower()

def generate_package(package_name: str, grammar_name: str, output_dir: Path) -> bool:
    """Generate parser package from template
        0. Create folder named {{grammar_name|lower}} (rm -r if it already exists)
        0. Copy files from template into generated folder
        1. Substitute {{template_variables}}: antlr_jar_file, grammar_name, grammar_name_lower, entry_rule
        2. Run setup build
    """
    my_dir = Path(__file__).parent
    template_package = my_dir/'templates'/'parser_package'
    grammar_relative_path = Path('src')/'grammar'

    log.info('Generating package files...')
    jj_env = jj.Environment(
        loader=jj.FileSystemLoader(template_package),
        undefined=jj.StrictUndefined
    )
    # grammar_snake_case = snake_case(grammar_name)
    try:
        output_dir.mkdir(exist_ok=True)
        context = {
            "grammar_name": grammar_name,
        }

        # Copy template package files and rename directories with passed-in values
        package_dir = output_dir/package_name
        if package_dir.exists():
            if not _DEBUG:
                log.error('Package directory exists, delete it first: "%s"', package_dir)
            else:
                shutil.rmtree(package_dir)
        path = shutil.copytree(template_package, package_dir)
        if not path:
            raise OSError
        # Rename grammar directory inside package_dir
        grammar_dir_copy = output_dir/package_name/'src'/'grammar'
        grammar_dir = output_dir/package_name/'src'/grammar_name.lower()
        grammar_dir_copy.rename(grammar_dir)

        # Overwrite top level package template files in output_dir
        for template_file in ('MANIFEST.in', 'README.md', 'setup.py'):
            template = jj_env.get_template(template_file)
            stream = template.stream(context)
            stream.dump(str(package_dir/template_file))

        # Overwrite grammar template files in output_dir
        for template_file in ('benchmark.pyt', 'print_tree.pyt'):
            template = jj_env.get_template(str(grammar_relative_path/template_file))
            stream = template.stream(context)
            template_path = grammar_dir/template_file
            stream.dump(str(template_path.with_suffix('.py')))
            template_path.unlink()

    except OSError:
        log.error('Error generating package directory/files in {}'.format(package_dir))
        return False

    return True

def generate_antlr(java_exe: Path, antlr_jar: Path, output_dir: Path, grammar_file: Path, lexer_file: Optional[Path]) -> bool:
    """Generate Python and C++ parsers using ANTLR and return True if successful"""
    try:
        # return_cwd = os.getcwd()
        cpp_dir = output_dir/'cpp_src'
        # cpp_dir.mkdir(parents=True, exist_ok=True)
        # os.chdir(output_dir)
        # shutil.copy(str(grammar_file), str(output_dir))
        # if lexer_file:
        #     shutil.copy(str(lexer_file), str(output_dir))
        antlr4 = '{} -Xmx500M -cp {} org.antlr.v4.Tool -Dlanguage={{}} -o {{}} {{}} {{}}'.format(java_exe, antlr_jar)
        if lexer_file:
            subprocess.run(antlr4.format('Python3', output_dir, '', lexer_file).split())
            subprocess.check_output(antlr4.format('Cpp', cpp_dir, '', lexer_file), shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(antlr4.format('Python3', output_dir, '-no-visitor -no-listener',
                                grammar_file), shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output(antlr4.format('Cpp', cpp_dir, '-visitor -no-listener',
                                grammar_file), shell=True, stderr=subprocess.STDOUT)
    except OSError as exception:
        log.error('ANTLR generation failed: %s', exception.strerror)
        return False
    except subprocess.CalledProcessError as exception:
        log.error('ANTLR generation failed: %s', exception.output)
        return False
    finally:
        # os.chdir(return_cwd)
        pass

    return True

def generate_extension(py_parser_path: Path, cpp_output_dir: Path, entry_rules: List[str]=None):
    log.info('Generating C++ extension...')
    speedy_antlr_tool.generate(
        py_parser_path=py_parser_path,
        cpp_output_dir=cpp_output_dir,
        entry_rule_names=entry_rules
    )
    return True

def build_extension(project_dir: Path, verbose:bool=False) -> bool:
    log.info('Building C++ extension (be patient, this can be slow)...')
    return_cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        if verbose:
            capture = None
        else:
            capture = subprocess.PIPE
        _ = subprocess.run([sys.executable, 'setup.py', 'build'], stdout=capture, stderr=capture)
    except OSError as exception:
        log.error('Error building extension: %s', exception.strerror)
        return False
    except subprocess.CalledProcessError as exception:
        log.error('Build failed: %s', exception.output)
        return False
    finally:
        os.chdir(return_cwd)

    return True


def test_grammar(grammar_name: str, input_file: str):
    'Test given grammar'
    # TODO: Finish this

    import grammar_name

    grammar_name.print_tree(input_file)
    grammar_name.benchmark(input_file, 1000)
    #TODO: compare parse tree?
    # with self.assertRaises(SystemExit) as context:
    #     self.run_compiler(args, check_errors=False)
    # self.assertEqual(context.exception.code, 0)


def main(argv: List[str]) -> int:
    """Parse command line options and do the work

    :param argv: list of command line arguments, not including program name (pass "-h" for help printout)
    :return: nonzero if error
    """
    argp = argparse.ArgumentParser(
        description='Given ANTLR grammar, create package with C++ extension and setup.py')
    argp.add_argument('grammar', type=Path,
                    help='ANTLR grammar file')
    argp.add_argument('-l', '--lexer', type=Path,
                    help='ANTLR lexer file (if separate from grammar)')
    argp.add_argument('-r', '--rules', type=str, nargs='+',
                    help='one or more entry rules')
    argp.add_argument('-p', '--packagename', type=str, default='generated_package',
                    help='name of package to generate')
    argp.add_argument('-a', '--antlrjar', type=Path, required=True,
                    help='ANTLR tool jar file')
    argp.add_argument('-o', '--outdir', type=Path, default='.',
                    help='directory to contain package contents')
    argp.add_argument('-j', '--javaexe', type=Path, default='java',
                    help='java executable file')
    argp.add_argument('-v', '--verbose', action='store_true',
                    help='print extra info')

    args = argp.parse_args(argv)

    if args.verbose:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)

    # Check that paths exist
    if not args.outdir.is_dir():
        if args.outdir.is_file():
            argp.error('Invalid output directory: "{}"'.format(args.outdir))
        else:
            try:
                args.outdir.mkdir()
            except OSError:
                argp.error('Unable to create output directory: "{}"'.format(args.outdir))

    try:
        grammar_text = args.grammar.read_text()
        match = re.search(r'(parser\s+|lexer\s+)?grammar\s+(\w+)\s*;', grammar_text)
        if match is None:
            log.error('Unable to parse grammar name from file "%s"', args.grammar)
        grammar_name = match.group(2)
    except OSError:
        argp.error('Unable to read grammar file: "{}"'.format(args.grammar))

    package_dir = args.outdir/args.packagename
    parser_dir = package_dir/'src'/grammar_name.lower()/'parser'
    grammar_file_name = grammar_name + 'Parser.py'
    py_parser_path = (parser_dir/grammar_file_name)
    if not args.verbose:
        print('Generating and building parser. Be patient, this can be very slow...')
    success = (
        generate_package(args.packagename, grammar_name, args.outdir) and (
        generate_antlr(args.javaexe, args.antlrjar, parser_dir, args.grammar, args.lexer)) and (
        generate_extension(py_parser_path, parser_dir/'cpp_src', args.rules)) and (
        build_extension(package_dir, args.verbose)
        )
    )
    if not success:
        print('ERRORS FOUND. Progress is in "{}"'.format(package_dir), file=sys.stderr)
        return 1
    log.info('Finished. Output is in "%s"', package_dir)

    return 0

if __name__ == '__main__':
    err = main(sys.argv[1:])
    logging.shutdown()
    sys.exit(err)
