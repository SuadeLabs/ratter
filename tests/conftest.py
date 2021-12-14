import ast
import os
import sys
import pytest

from contextlib import contextmanager
from os.path import dirname, join

import ratter

from ratter.analyser.base import CustomFunctionAnalyser, CustomFunctionHandler
from ratter.analyser.context import Context, RootContext
from ratter.analyser.context.symbol import Call, Name
from ratter.analyser.types import FileIR, FuncOrAsyncFunc, FunctionIR
from ratter.analyser.util import LOCAL_VALUE_PREFIX


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "pypy: mark test to run only under pypy"
    )
    config.addinivalue_line(
        "markers", "py_3_8_plus: mark test to run only under Python 3.8+"
    )


def pytest_collection_modifyitems(config, items):
    """Alter the collected tests."""
    # If this is pypy, enable the tests which require pypy
    pypy_items = list()
    non_pypy_items = list()

    for item in items:
        if item.get_closest_marker("pypy"):
            pypy_items.append(item)
        else:
            non_pypy_items.append(item)

    if is_pypy():
        items[:] = pypy_items + non_pypy_items
    else:
        items[:] = non_pypy_items

    # If this is Python 3.8+, enable Python 3.8+ tests
    py_lte_3_7_tests = list()
    py_gte_3_8_tests = list()

    for item in items:
        if item.get_closest_marker("py_3_8_plus"):
            py_gte_3_8_tests.append(item)
        else:
            py_lte_3_7_tests.append(item)

    if is_python_3_8_plus():
        items[:] = py_lte_3_7_tests + py_gte_3_8_tests
    else:
        items[:] = py_lte_3_7_tests


def is_pypy():
    """Return `True` if running under pypy."""
    try:
        import __pypy__
        return True
    except ModuleNotFoundError:
        return False


def is_python_3_8_plus():
    """Return `True` if running under Python 3.8 plus."""
    if sys.version_info.major != 3:
        raise NotImplementedError

    if sys.version_info.minor >= 8:
        return True
    else:
        return False


@pytest.fixture
def parse():
    def _inner(source: str) -> ast.AST:
        """Return the parsed AST for the given code, use relative indentation.

        Assume usage is:
            parse('''
                <source code>       # first line sets the base indent
                <source code>
                    <source code>   # this is indented once (relative)
                <source code>
            ''')

        Require the opening and closing blank lines.
        """
        lines = list()
        source_lines = source.splitlines()[1:-1]

        if not len(source_lines):
            raise ValueError("Incorrect source code formatting")

        # Determine whitespace from first line
        indent = str()
        for c in source_lines[0]:
            if not c.isspace():
                break
            indent += c

        # Strip whitespace from all lines
        for line in source_lines:
            if line.startswith(indent):
                lines.append(line[len(indent):])
            elif line == "":
                lines.append(line)
            else:
                raise SyntaxError("Incorrect indentation in test code")

        return ast.parse("\n".join(lines))

    return _inner


@pytest.fixture
def RootSymbolTable():
    def _inner(*args):
        """Create a root context with the addition of the **kwargs."""
        symtab = RootContext(ast.Module(body=[])).symbol_table

        for s in args:
            symtab.add(s)

        return symtab

    return _inner


@pytest.fixture
def config():

    @contextmanager
    def _inner(attr, value):
        if not hasattr(ratter.config, attr):
            raise AttributeError

        _previous = getattr(ratter.config, attr)
        setattr(ratter.config, attr, value)
        yield
        setattr(ratter.config, attr, _previous)

    return _inner


@pytest.fixture
def stdlib_modules():
    # Scraped from python.org
    scraped = {
        'string',
        're',
        'difflib',
        'textwrap',
        'unicodedata',
        'stringprep',
        'rlcompleter',
        'struct',
        'codecs',
        'datetime',
        'calendar',
        'collections',
        'abc',
        'heapq',
        'bisect',
        'array',
        'weakref',
        'types',
        'copy',
        'pprint',
        'reprlib',
        'enum',
        'numbers',
        'math',
        'cmath',
        'decimal',
        'fractions',
        'random',
        'statistics',
        'itertools',
        'functools',
        'operator',
        'pathlib',
        'fileinput',
        'stat',
        'filecmp',
        'tempfile',
        'glob',
        'fnmatch',
        'linecache',
        'shutil',
        'pickle',
        'copyreg',
        'shelve',
        'marshal',
        'dbm',
        'sqlite3',
        'zlib',
        'gzip',
        'bz2',
        'lzma',
        'zipfile',
        'tarfile',
        'csv',
        'configparser',
        'netrc',
        'xdrlib',
        'plistlib',
        'hashlib',
        'hmac',
        'secrets',
        'os',
        'io',
        'time',
        'argparse',
        'getopt',
        'logging',
        'getpass',
        'curses',
        'platform',
        'errno',
        'ctypes',
        'threading',
        'multiprocessing',
        'concurrent',
        'subprocess',
        'sched',
        'queue',
        '_thread',
        'asyncio',
        'asyncio',
        'socket',
        'ssl',
        'select',
        'selectors',
        'asyncore',
        'asynchat',
        'signal',
        'mmap',
        'email',
        'json',
        'mailcap',
        'mailbox',
        'mimetypes',
        'base64',
        'binhex',
        'binascii',
        'quopri',
        'uu',
        'html',
        'webbrowser',
        'cgi',
        'cgitb',
        'wsgiref',
        'urllib',
        'http',
        'ftplib',
        'poplib',
        'imaplib',
        'nntplib',
        'smtplib',
        'smtpd',
        'telnetlib',
        'uuid',
        'socketserver',
        'xmlrpc',
        'ipaddress',
        'audioop',
        'aifc',
        'sunau',
        'wave',
        'chunk',
        'colorsys',
        'imghdr',
        'sndhdr',
        'ossaudiodev',
        'gettext',
        'locale',
        'turtle',
        'cmd',
        'shlex',
        'typing',
        'pydoc',
        'doctest',
        'unittest',
        '2to3',
        'test',
        'bdb',
        'faulthandler',
        'pdb',
        'timeit',
        'trace',
        'tracemalloc',
        'distutils',
        'venv',
        'zipapp',
        'sys',
        'sysconfig',
        'builtins',
        'warnings',
        'dataclasses',
        'contextlib',
        'abc',
        'atexit',
        'traceback',
        'gc',
        'inspect',
        'site',
        'code',
        'codeop',
        'zipimport',
        'pkgutil',
        'modulefinder',
        'runpy',
        'importlib',
        'ast',
        'symtable',
        'token',
        'keyword',
        'tokenize',
        'tabnanny',
        'pyclbr',
        'py_compile',
        'compileall',
        'dis',
        'pickletools',
        'spwd',
        'crypt',
        'tty',
        'pty',
        'pipes',
        'nis',
        'optparse',
        'imp',
        'six',
    }

    # Python 3.10 removed a lot of stdlib modules
    if sys.version_info.major == 3 and sys.version_info.minor <= 9:
        scraped.union({
            '_dummy_thread',
            'dummy_threading',
            'formatter',
            'parser',
            'symbol',
        })

    # Some stdlib modules are not on Windows
    if os.name != "nt":
        scraped.union({
            'posix',
            'resource',
            'grp',
            'fcntl',
            'readline',
            'termios',
            'pwd',
            'syslog',
        })

    return scraped


@pytest.fixture
def builtins():
    generated = {
        'abs',
        'all',
        'any',
        'ascii',
        'bin',
        'bool',
        'breakpoint',
        'bytearray',
        'bytes',
        'callable',
        'chr',
        'classmethod',
        'compile',
        'complex',
        'copyright',
        'credits',
        'delattr',
        'dict',
        'dir',
        'divmod',
        'enumerate',
        'eval',
        'exec',
        'filter',
        'float',
        'format',
        'frozenset',
        'getattr',
        'globals',
        'hasattr',
        'hash',
        'help',
        'hex',
        'id',
        'input',
        'int',
        'isinstance',
        'issubclass',
        'iter',
        'len',
        'license',
        'list',
        'locals',
        'map',
        'max',
        'memoryview',
        'min',
        'next',
        'object',
        'oct',
        'open',
        'ord',
        'pow',
        'print',
        'property',
        'range',
        'repr',
        'reversed',
        'round',
        'set',
        'setattr',
        'slice',
        'sorted',
        'staticmethod',
        'str',
        'sum',
        'super',
        'tuple',
        'type',
        'vars',
        'zip'
    }

    return generated


@pytest.fixture
def snippet():
    def _inner(relative_path: str):
        return join(dirname(__file__), "snippets", relative_path)

    return _inner


@pytest.fixture
def file_ir_from_dict():
    def _inner(ir):
        # Make quasi-context
        ctx = Context(None)
        ctx.add_all(ir.keys())

        # Create FileIR
        file_ir = FileIR(ctx)
        file_ir._file_ir = ir

        return file_ir

    return _inner


class _PrintBuiltinAnalyser(CustomFunctionAnalyser):

    @property
    def name(self) -> str:
        return "print"

    @property
    def qualified_name(self) -> str:
        return "print"

    def on_def(self, name: str, node: FuncOrAsyncFunc, ctx: Context) -> FunctionIR:
        return {
            "sets": {
                Name("set_in_print_def"),
            },
            "gets": {
                Name("get_in_print_def"),
            },
            "dels": {
                Name("del_in_print_def"),
            },
            "calls": {
                Call("call_in_print_def", [], {}, None),
            },
        }

    def on_call(self, name: str, node: ast.Call, ctx: Context) -> FunctionIR:
        return {
            "sets": {
                Name("set_in_print"),
            },
            "gets": {
                Name("get_in_print"),
            },
            "dels": {
                Name("del_in_print"),
            },
            "calls": {
                Call("call_in_print", [], {}, None),
            },
        }


@pytest.fixture
def PrintBuiltinAnalyser():
    return _PrintBuiltinAnalyser


class _ExampleFuncAnalyser(CustomFunctionAnalyser):

    @property
    def name(self) -> str:
        return "example"

    @property
    def qualified_name(self) -> str:
        return "module.example"

    def on_def(self, name: str, node: FuncOrAsyncFunc, ctx: Context) -> FunctionIR:
        return {
            "sets": {
                Name("set_in_example_def"),
            },
            "gets": {
                Name("get_in_example_def"),
            },
            "dels": {
                Name("del_in_example_def"),
            },
            "calls": {
                Call("call_in_example_def", [], {}, None),
            },
        }

    def on_call(self, name: str, node: ast.Call, ctx: Context) -> FunctionIR:
        return {
            "sets": {
                Name("set_in_example"),
            },
            "gets": {
                Name("get_in_example"),
            },
            "dels": {
                Name("del_in_example"),
            },
            "calls": {
                Call("call_in_example", [], {}, None),
            },
        }


@pytest.fixture
def ExampleFuncAnalyser():
    return _ExampleFuncAnalyser


@pytest.fixture
def handler():
    handler = CustomFunctionHandler(
        [_PrintBuiltinAnalyser()],
        [_ExampleFuncAnalyser()]
    )

    return handler


@pytest.fixture
def constant():
    """Return the version specific name for a constant of the given type.

    In Python <= 3.7, constants are named as such "@Str", "@Num", etc.

    In Python >= 3.8, constants are all named "@Constant".

    """

    def _inner(node_type: str):
        if sys.version_info.major != 3:
            raise AssertionError

        if sys.version_info.minor <= 7:
            return f"{LOCAL_VALUE_PREFIX}{node_type}"
        else:
            return f"{LOCAL_VALUE_PREFIX}Constant"

    return _inner
