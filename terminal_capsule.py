"""TerminalCapsule: CAPTURE, PLAYBACK, and VALIDATE I/O for ProcessCapsule."""

from json import (
    dump as json_dump,
    load as json_load,
)
from sys import (
    stdin as _input_from_user,
    stdout as _output_to_user,
)
from select import select as _select

from process_capsule import PythonCapsule as Capsule

__author__ = "Minho Ryang (minhoryang@gmail.com)"


class _TerminalCapsuleUtils(object):
    """(Internal) Utils for Terminal Capsule."""

    @staticmethod
    def register(chained=None):
        """@register()"""
        def _register(func1):
            target = func1
            if chained:
                target = chained(func1)
            _Registered[func1.__name__.lower()] = target
            return func1
        return _register

    class pprintify(object):
        """@pprintify"""
        def __init__(self, f):
            self.f = f
            self.__name__ = f.__name__

        def __call__(self, *args, **kwargs):
            from pprint import pprint
            pprint(self.f(*args, **kwargs))

    @staticmethod
    def endpoints(pair_from_capsule, log=None):
        """Capsule's in/out would be handled in here by printing or logging."""
        if pair_from_capsule:
            stdin, stdout = pair_from_capsule
            if isinstance(stdout, (bytes)):
                # TODO: XXX: WHY DON'T CHARDET?
                _output_to_user.write(stdout.decode("utf-8"))
            else:
                _output_to_user.write(str(stdout))
            _output_to_user.flush()
            if log is not None:
                log.append(pair_from_capsule)

    @staticmethod
    def hook(capsule, timeout=None):
        """Hook user's input between terminal and capsule, Get outputs."""
        is_readable, _, _ = _select([_input_from_user], [], [], 0)
        if is_readable:
            terminal_stdin = _input_from_user.readline().rstrip()
            try:
                _, capsule_stdout = capsule.write(
                    terminal_stdin,
                    timeout=timeout,
                )
            except Capsule.DEAD as dying_message:
                capsule_stdout = str(dying_message)
            return (terminal_stdin, capsule_stdout)
        else:
            try:
                capsule_stdout = capsule.read(timeout=timeout)
            except Capsule.DEAD as dying_message:
                capsule_stdout = str(dying_message)
            if capsule_stdout:
                return (None, capsule_stdout)

    @staticmethod
    def stream(capsule, captured_stdin, timeout=None):
        """Stream captured stdin to capsule and Get outputs."""
        try:
            if captured_stdin:
                _, capsule_stdout = capsule.write(
                    captured_stdin,
                    timeout=timeout,
                )
                return (captured_stdin, capsule_stdout)
            return (None, capsule.read(timeout=timeout))
        except Capsule.DEAD as dying_message:
            return (captured_stdin, str(dying_message))


_Registered = {}


@_TerminalCapsuleUtils.register(_TerminalCapsuleUtils.pprintify)
def Capture(this_program, to_json=None):
    """Run `this_program` by ProcessCapsule and Capture I/O `to_json`."""
    captured = []
    with Capsule(this_program) as terminal:
        terminal.run(with_check=False)
        while not terminal.is_dead():
            _TerminalCapsuleUtils.endpoints(
                _TerminalCapsuleUtils.hook(terminal),
                captured,
            )
    if to_json:
        with open(to_json, 'w') as json_fp:
            json_dump(captured, json_fp)
    return captured


@_TerminalCapsuleUtils.register()
def Playback(this_program, from_json):
    """Read I/O `from_json` and Playback it to `this_program`."""
    if from_json is None:
        raise Exception("-j, --json needed!")

    with open(from_json, 'r') as fp:
        captured = json_load(fp)
        with Capsule(this_program) as terminal:  # TODO: logging
            terminal.run(with_check=False)
            for captured_stdin, _ in captured:
                _TerminalCapsuleUtils.endpoints(
                    _TerminalCapsuleUtils.stream(
                        terminal,
                        captured_stdin,
                    ),
                )
            while not terminal.is_dead():
                _TerminalCapsuleUtils.endpoints(
                    _TerminalCapsuleUtils.stream(
                        terminal,
                        None,
                    )
                )


@_TerminalCapsuleUtils.register()
def Validate(this_program, from_json):
    """Read I/O `from_json` and Validate it to `this_program`."""
    if from_json is None:
        raise Exception("-j, --json needed!")

    with open(from_json, 'r') as fp:
        captured = json_load(fp)

        class DB:  # TODO: Rename 'TerminalValidateStatus'
            _now = 0
            _max = len(captured)
            _retries = 0
            _max_retries = 50  # TODO
            _borrow = None
        db = DB()

        @_TerminalCapsuleUtils.pprintify
        def _FAIL(captured, db, expected, stdout):
            print('[FAIL] %d' % (db._now))
            return {
                'now_expected': expected,
                'orig_expected': captured[db._now][1],
                'stdout': stdout,
                'borrow': db._borrow
            }

        def _PASS(db):
            print('[PASS] %d' % (db._now))
            db._now += 1
            db._retries = 0
            db._borrow = None

        def _RETRIES(captured, db, expected, stdout):
            db._retries += 1
            if db._retries >= db._max_retries:
                _FAIL(captured, db._now, expected, stdout)

        with Capsule(this_program, logfile=open("test.log", "wb")) as terminal:
            db._borrow = terminal.run()
            stdin = None
            expected = None
            while db._now < db._max:
                if not db._retries:
                    stdin, expected = captured[db._now]
                    print('-----')
                    print('Input %d %s' % (
                        db._now,
                        stdin.encode('utf-8') if stdin else None,
                    ))
                    print('Expected %d %s' % (
                        db._now,
                        expected.encode('utf-8'),
                    ))
                    _, stdout = _TerminalCapsuleUtils.stream(terminal, stdin)
                else:
                    _, stdout = _TerminalCapsuleUtils.stream(terminal, None)
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
                    elif stdout and len(stdout) > len(expected):
                        if stdout[:len(expected)] == expected:
                            _PASS(db)
                            print('[LEFT] %d' % (db._now))
                            db._borrow = stdout[len(expected):]
                        else:
                            _FAIL(captured, db, expected, stdout)
                            break
                    elif stdout:
                        _FAIL(captured, db, expected, stdout)
                        break
                    else:
                        _RETRIES(captured, db, expected, stdout)


if __name__ == "__main__":
    from click import (
        argument,
        command,
        option,
        Choice,
        Path,
    )

    @command()
    @argument('program', type=Path())
    @option('-j', '--json', type=Path(), default=None)
    @option('-m', '--mode',
            'mode', type=Choice(_Registered.keys()), default='capture')
    def __main__(program, json=None, mode=False):
        """Entrypoint for Terminal Capsule."""
        _Registered[mode](program, json)

    __main__()
