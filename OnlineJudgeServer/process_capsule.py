"""Process Capsule: The PExpect Wrapper."""

from errno import ESRCH as NoSuchProcess
from os import kill, environ
from os.path import join
from signal import SIGTERM as CTRL_C

from chardet import detect as Chardet
from pexpect import (
    spawn,
    TIMEOUT,
    EOF,
)

__author__ = "Minho Ryang (minhoryang@gmail.com)"


class ProcessCapsule(object):
    """Process Capsule: The PExpect Wrapper.

    It's designed for
    - receiving stderr
    - detecting segfault++
    - dying gracefully.

    >>> with ProcessCapsule('a.out') as process:
    ...     process.run()
    ...     process.read()
    """

    _SEGFAULT = '.*Segmentation fault.*'
    _CONDITIONS = [_SEGFAULT, EOF, TIMEOUT]
    _TIMEOUT = .05

    def __init__(self, program, logfile=None):
        self.program = program
        self.logfile = logfile
        self._readpos = 0
        self._runtime = None
        self._initialized_pid = None

    def __del__(self):
        """Rest in peace, you're going to **die gracefully**."""
        if self._initialized_pid:
            try:
                kill(self._initialized_pid, CTRL_C)
            except OSError as exc:
                if exc.errno != NoSuchProcess:
                    raise exc

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.__del__()

    def __cmd__(self):
        return 'bash -c "./%s 2>&1 #%s"' % (self.program, self)

    def run(self, with_check=True, flush_by_read=True, timeout=None):
        """First of all, **Show must go on**, whether you like it or not."""
        if self._initialized_pid:
            raise self.ALREADYLAUNCHED()

        self._runtime = spawn(
            self.__cmd__(),
            logfile=self.logfile,
            ignore_sighup=False)
        self._initialized_pid = self._runtime.pid
        if with_check:
            return self.__try_read__(with_read=flush_by_read, timeout=timeout)

    def read(self, timeout=None):
        """Returns the text from stdin/stdout/stderr streams."""
        try:
            if self._initialized_pid:
                self.__try_read__(with_read=False, timeout=timeout)
            else:
                self.run(flush_by_read=False)
        except self.Exceptions as handling_my_excptions_only:
            raise handling_my_excptions_only
        return self.__readpos__()

    def write(self, this="", response=True, timeout=None):
        """Returns with/without @response."""
        if not self._initialized_pid:
            self.run()  # flushed

        retval = self._runtime.sendline(this)
        if response:
            return (retval, self.__try_read__(timeout=timeout))
        return (retval, None)

    def expect(self, queries, where=None, timeout=None):
        """Returns expected (@query, @where)."""
        if not self._initialized_pid:
            self.run()  # flushed

        text = where if where else self.__try_read__(timeout=timeout)
        if isinstance(queries, (list, tuple)):
            for query in queries:
                if query in text:
                    return (query, text)
        elif isinstance(queries, str):
            for queries in text:
                return (queries, text)

        return (None, text)

    def __try_read__(self, with_read=True, timeout=None):
        """Every steps you take, watch out! (SegFault, Dead, ...)"""
        if not self._initialized_pid:
            self.run(with_check=False)

        selected = self._runtime.expect(
            self._CONDITIONS,
            timeout=self._TIMEOUT if not timeout else timeout
        )

        if self._CONDITIONS[selected] == self._SEGFAULT:
            self._runtime.close()
            # TODO: Propagate self._runtime.exitstatus .signalstatus
            raise self.SEGFAULT(self.__readpos__())
        elif self._CONDITIONS[selected] == EOF:
            raise self.DEAD(self.__readpos__())
        elif with_read:
            return self.read()

    def __readpos__(self):
        """Read from **just before**."""
        current = len(self._runtime.before)
        wanted = self._runtime.before[self._readpos:current]
        self._readpos = current
        det = Chardet(wanted)
        if det['encoding']:
            return wanted.decode(det['encoding'])
        return wanted.decode('utf-8')  # TODO

    def is_dead(self):
        return not self._runtime.isalive()

    class Exceptions(Exception):
        """Grouping all exceptions controlled by here."""
    class SEGFAULT(Exceptions):
        """Fired when SegFault detected."""
    class DEAD(Exceptions):
        """Fired when dead unexpectedly."""
    class ALREADYLAUNCHED(Exceptions):
        """Fired when calling run() more than once."""


DEFAULT_PYTHON = 'python'
if environ['VIRTUAL_ENV']:
    DEFAULT_PYTHON = join(environ['VIRTUAL_ENV'], 'bin/python')


class PythonCapsule(ProcessCapsule):
    def __init__(self, program, logfile=None, python=DEFAULT_PYTHON):
        super().__init__(program, logfile=logfile)
        self.python = python

    def __cmd__(self):
        return 'bash -c "%s -u %s 2>&1 #%s"' % (
            self.python,
            self.program,
            self,
        )


def prompt_spliter(result, cmd='', prompt='', splits='\n'):
    """Split the output without prompt environment.

    For removing all empty results, using filter method.
    Learned from:
    stackoverflow.com/questions/3845423/remove-empty-strings-from-a-list-of-strings
    """
    output = []
    for i in result.split(splits):
        output.append(i.strip())
    for _ in range(output.count(cmd)):
        output.remove(cmd)
    for _ in range(output.count(prompt)):
        output.remove(prompt)
    return list(filter(None, output))
