from sys import (
    stdin as _stdin,
    stdout as _stdout,
)
from select import select
from json import (
    dump as json_dump,
    load as json_load,
)
from pprint import pprint

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


def _in_out_hook(terminal, log=None, timeout=.05):
    """try to read from user, send it to program."""
    # try to read stdin
    stdin, _, _ = select([_stdin], [], [], 0)
    if stdin:
        stdin = stdin[0].readline().rstrip()
        try:
            stdout = terminal.write(stdin, timeout=timeout)[1]
        except PC.DEAD as e:
            stdout = str(e)
        if log is not None:
            log.append((stdin, stdout))
    else:
        try:
            stdout = terminal.read(timeout=timeout)
        except PC.DEAD as e:
            stdout = str(e)
        if stdout and log is not None:
            log.append((None, stdout))
    return stdout


def _in_out_stream(terminal, stdin, stdout, timeout=.05):
    try:
        if stdin:
            return terminal.write(stdin, timeout=timeout)[1]
        return terminal.read(timeout=timeout)
    except PC.DEAD as e:
        return str(e)


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
        from pprint import pprint
        pprint(
            terminal_capture(program, json)
        )
    elif mode == 'playback':
        terminal_playback(program, json)
    elif mode == 'validate':
        terminal_validate(program, json)


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
                _feedback_to_user(_in_out_stream(terminal, stdin, None))
            while not terminal.is_dead():
                _feedback_to_user(_in_out_stream(terminal, None, None))


def terminal_validate(program, json):
    if json is None:
        raise Exception("-j, --json needed!")
    with open(json, 'r') as fp:
        captured = json_load(fp)

        class DB:
            _now = 0
            _max = len(captured)
            _retries = 0
            _max_retries = 50  # TODO
            _borrow = None
        db = DB()
        with PC(program, logfile=open("test.log", "wb")) as terminal:
            terminal.run(with_check=False)  # TODO
            stdin = None
            expected = None
            while db._now < db._max:
                if not db._retries:
                    stdin, expected = captured[db._now]
                    print('-----')
                    print('Input %d %s' % (db._now, stdin.encode('utf-8') if stdin else None))
                    print('Expected %d %s' % (db._now, expected.encode('utf-8')))
                    stdout = _in_out_stream(terminal, stdin, None)
                else:
                    stdout = _in_out_stream(terminal, None, None)
                if db._borrow:
                    stdout = db._borrow + stdout
                    db._borrow = None
                print('Output %d %s' % (db._now, stdout.encode('utf-8')))
                if stdout == expected:
                    _PASS(db)
                else:
                    # partial check
                    if stdout and len(stdout) < len(expected):
                        if expected[:len(stdout)] == stdout:
                            print('[PARTIAL] %d' % (db._now))
                            expected = expected[len(stdout):]
                            _RETRIES(captured, db, expected, stdout)
                        else:
                            _FAIL(captured, db, expected, stdout)
                            break
                    elif len(stdout) > len(expected):
                        if stdout[:len(expected)] == expected:
                            _PASS(db)
                            print('[LEFT] %d' % (db._now))
                            db._borrow = stdout[len(expected):]
                        else:
                            _FAIL(captured, db, expected, stdout)
                            break
                    else:
                        _FAIL(captured, db, expected, stdout)
                        break


def _FAIL(captured, db, expected, stdout):
    print('[FAIL] %d' % (db._now))
    pprint({'now_expected': expected, 'orig_expected': captured[db._now][1], 'stdout': stdout, 'borrow': db._borrow})


def _PASS(db):
    print('[PASS] %d' % (db._now))
    db._now += 1
    db._retries = 0
    db._borrow = None


def _RETRIES(captured, db, expected, stdout):
    db._retries += 1
    if db._retries >= db._max_retries:
        _FAIL(captured, db._now, expected, stdout)


if __name__ == "__main__":
    terminal()
