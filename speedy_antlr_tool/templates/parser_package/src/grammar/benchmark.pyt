import timeit

import antlr4

from .parser import sa_{{grammar_name|lower}}


def benchmark(input_file:str, entry_rule:str, count=100):

    cpp_elapsed = timeit.timeit(lambda: sa_{{grammar_name|lower}}._cpp_parse(antlr4.FileStream(input_file), entry_rule), number=count)
    py_elapsed = timeit.timeit(lambda: sa_{{grammar_name|lower}}._py_parse(antlr4.FileStream(input_file), entry_rule), number=count)

    py_elapsed = py_elapsed / count
    cpp_elapsed = cpp_elapsed / count

    print("py_elapsed:  %.3f" % (py_elapsed * 1000), "ms")
    print("cpp_elapsed: %.3f" % (cpp_elapsed * 1000), "ms")
    print("Speedup: %.2f" % (py_elapsed / cpp_elapsed))
