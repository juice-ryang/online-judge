from sys import (
    stdin as _stdin,
    stdout as _stdout,
)
import json
from select import select

from process_capsule import PythonCapsule as PC


def stdout(stdout):
    """."""
    if isinstance(stdout, (bytes)):
        _stdout.write(stdout.decode("utf-8"))
    else:
        _stdout.write(str(stdout))
    _stdout.flush()

def stdin(log=None):
    """try to read from user, send it to program."""
    # try to read stdin
    stdin, _, _ = select([_stdin], [], [], 0)
    if stdin:
        stdin = stdin[0].readline().rstrip()
        stdout = a.write(stdin)[1]
        if log is not None:
            log.append((stdin, stdout))
    else:
        stdout = a.read()
        if stdout != b'' and log is not None:
            log.append((None, stdout))
    return stdout


a = PC("test5.py")
a.run(with_check=False)
b = []
while not a.is_dead():
    stdout(stdin(b))
from pprint import pprint
pprint(b)
