from sys import (
    stdin as _stdin,
    stdout as _stdout,
)
from select import select
from json import (
    dump as json_dump,
    load as json_load,
)

from click import (
    argument,
    command,
    option,
    Choice,
    Path,
)

from process_capsule import PythonCapsule as PC


def _feedback_to_user(stdout):
    """."""
    if isinstance(stdout, (bytes)):
        _stdout.write(stdout.decode("utf-8"))
    else:
        _stdout.write(str(stdout))
    _stdout.flush()


def _in_out_hook(terminal, log=None):
    """try to read from user, send it to program."""
    # try to read stdin
    stdin, _, _ = select([_stdin], [], [], 0)
    if stdin:
        stdin = stdin[0].readline().rstrip()
        stdout = terminal.write(stdin)[1]
        if log is not None:
            log.append((stdin, stdout))
    else:
        stdout = terminal.read()
        if stdout != b'' and log is not None:
            log.append((None, stdout))
    return stdout


def _in_out_stream(terminal, stdin, stdout):
    if stdin:
        terminal.write(stdin, response=False)
    return terminal.read(timeout=1)


@command()
@argument('program', type=Path())
@option('-j', '--json', type=Path(), default=None) 
@option('--mode', 'mode', type=Choice([
    'capture',
    'playback',
    'validate',
]), default='capture')
def terminal(program, json=None, mode=False):
    if mode == 'capture':
        terminal_capture(program, json)
    elif mode == 'playback':
        terminal_playback(program, json)
    elif mode == 'validate':
        pass  # TODO


def terminal_capture(program, json=None):
    captured = []
    with PC(program) as terminal:
        terminal.run(with_check=False)
        while not terminal.is_dead():
            _feedback_to_user(_in_out_hook(terminal, captured))
    if json:
        with open(json, 'w') as fp:
            json_dump(captured, fp)
    return captured


def terminal_playback(program, json):
    if json is None:
        raise Exception("-j, --json needed!")
    with open(json, 'r') as fp:
        captured = json_load(fp)
        with PC(program, logfile=open("test.log", "wb")) as terminal:
            terminal.run(with_check=False)
            for stdin, stdout in captured:
                # TODO : NOT YET TO WORK!
                _feedback_to_user(_in_out_stream(terminal, stdin, None))
            _feedback_to_user(_in_out_stream(terminal, None, None))


if __name__ == "__main__":
    terminal()
