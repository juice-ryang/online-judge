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
        """`Register to Menu` Decorator.

        >>> @register()
        ... def func1():
        ...     pass
        >>> @register(func1)
        ... def func2():
        ...     pass
        """
        def _register(func1):
            target = func1
            if chained:
                target = chained(func1)
            _Registered[func1.__name__.lower()] = target
            return func1
        return _register

    class pprintify(object):
        """`pprint()` Decorator.

        >>> @pprintify
        ... def func():
        ...     pass
        """
        def __init__(self, f):
            self.f = f

        def __repr__(self):
            return self.f.__repr__()

        def __call__(self, *args, **kwargs):
            from pprint import pprint
            ret = self.f(*args, **kwargs)
            pprint(ret)
            return ret

    @staticmethod
    def report(this):
        # XXX: no additional parameters
        def _(*args, **kwargs):
            # TODO: logging at here
            return this(*args, **kwargs)
        return _

    @staticmethod
    def endpoints(pair_from_capsule, records=None):
        """Capsule's in/out would be handled in here."""
        if pair_from_capsule:
            stdin, stdout = pair_from_capsule
            if isinstance(stdout, (bytes)):
                # TODO XXX: WHY DON'T CHARDET?
                _output_to_user.write(stdout.decode("utf-8"))
            else:
                _output_to_user.write(str(stdout))
            _output_to_user.flush()
            if records is not None:
                records.append(pair_from_capsule)

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
def Capture(this_program, to_json=None, logfile=None, timeout=None):
    """Run `this_program` by ProcessCapsule and Capture I/O `to_json`."""
    captured = []
    with Capsule(this_program, logfile=logfile) as capsule:
        capsule.run(with_check=False)
        while not capsule.is_dead():
            _TerminalCapsuleUtils.endpoints(
                _TerminalCapsuleUtils.hook(
                    capsule,
                    timeout=timeout,
                ),
                records=captured,
            )
    if to_json:
        with open(to_json, 'w') as json_fp:
            json_dump(captured, json_fp)
    return captured


@_TerminalCapsuleUtils.register()
def Playback(this_program, from_json, logfile=None, timeout=None):
    """Read I/O `from_json` and Playback it to `this_program`."""
    if from_json is None:
        raise Exception("-j, --json needed!")

    with open(from_json, 'r') as fp:
        captured = json_load(fp)
        with Capsule(this_program, logfile=logfile) as capsule:
            capsule.run(with_check=False)
            for captured_stdin, _ in captured:
                _TerminalCapsuleUtils.endpoints(
                    _TerminalCapsuleUtils.stream(
                        capsule,
                        captured_stdin,
                        timeout=timeout,
                    ),
                )
            while not capsule.is_dead():
                _TerminalCapsuleUtils.endpoints(
                    _TerminalCapsuleUtils.stream(
                        capsule,
                        None,
                        timeout=timeout,
                    )
                )


@_TerminalCapsuleUtils.register()
def Validate(this_program, from_json,
             logfile=None, max_retries=50, timeout=None,
             report=_TerminalCapsuleUtils.report):
    """Read I/O `from_json` and Validate it to `this_program`."""
    if from_json is None:
        raise Exception("-j, --json needed!")

    with open(from_json, 'r') as fp:
        captured = json_load(fp)

        class TerminalValidateStatus(object):
            """
            N: which captured line try to validate.
            RETRIES: for waiting slow response.
            """
            N = 0
            MAX = len(captured)
            RETRIES = 0

        class TerminalValidateBuffer(object):
            """
            expected: from captured
            stdout: from capsule
            borrow: left from stdout-expected
            """
            expected = None
            stdout = None
            borrow = None

        now = TerminalValidateStatus()
        buf = TerminalValidateBuffer()

        @report
        @_TerminalCapsuleUtils.pprintify
        def _FAIL():
            print('[FAIL] %d' % (now.N))
            return {
                'now_expected': buf.expected,
                'orig_expected': captured[now.N][1],
                'stdout': buf.stdout,
                'borrow': buf.borrow,
            }

        @report
        def _PASS():
            print('[PASS] %d' % (now.N))
            now.N += 1
            now.RETRIES = 0
            buf.borrow = None

        @report
        def _RETRIES():
            now.RETRIES += 1
            if now.RETRIES >= max_retries:
                return _FAIL()

        @report
        def _PARTIAL():
            print('[PARTIAL] %d' % (now.N))
            buf.expected = buf.expected[len(buf.stdout):]
            return _RETRIES()

        @report
        def _LEFT():
            _PASS()  # XXX order) be here!
            print('[LEFT] %d' % (now.N))
            buf.borrow = buf.stdout[len(buf.expected):]

        @report
        def _START():
            buf.borrow = capsule.run()  # XXX: no timeout!

        @report
        def _GET_STDIN():
            stdin, buf.expected = captured[now.N]
            print('-----')
            print('Input %d %s' % (
                now.N,
                stdin.encode('utf-8') if stdin else None,
            ))
            print('Expected %d %s' % (
                now.N,
                buf.expected.encode('utf-8'),
            ))
            return stdin

        @report
        def _GOT_STDOUT():
            if buf.borrow:
                buf.stdout = buf.borrow + buf.stdout
                buf.borrow = None
            print('Output %d %s' % (now.N, buf.stdout.encode('utf-8')))

        with Capsule(this_program, logfile=logfile) as capsule:
            _START()
            while now.N < now.MAX:
                if not now.RETRIES:
                    _, buf.stdout = _TerminalCapsuleUtils.stream(
                        capsule,
                        _GET_STDIN(),
                        timeout=timeout,
                    )
                else:
                    _, buf.stdout = _TerminalCapsuleUtils.stream(
                        capsule,
                        None,
                        timeout=timeout,
                    )
                _GOT_STDOUT()
                if buf.stdout == buf.expected:
                    _PASS()
                else:
                    if buf.stdout:  # XXX: Partial Check
                        if len(buf.stdout) < len(buf.expected):
                            if buf.expected[:len(buf.stdout)] == buf.stdout:
                                is_failed = _PARTIAL()
                                if is_failed:
                                    break
                            else:
                                _FAIL()
                                break
                        elif len(buf.stdout) > len(buf.expected):
                            if buf.stdout[:len(buf.expected)] == buf.expected:
                                _LEFT()
                            else:
                                _FAIL()
                                break
                        else:
                            _FAIL()
                            break
                    else:
                        is_failed = _RETRIES()
                        if is_failed:
                            break


if __name__ == "__main__":
    from click import (
        argument,
        command,
        option,
        Choice,
        File,
        Path,
    )

    @command()
    @argument('program', type=Path())
    @option('-m', '--mode',
            'mode', type=Choice(_Registered.keys()), default='capture')
    @option('-j', '--json', type=Path(), default=None,
            help='Generate .json (or playback/validate)')
    @option('-o', '--out', type=File('wb'), default=None,
            help='Generate .out  (or logging)')
    @option('-t', '--timeout', type=int, default=None,
            help='Set timeout (default: .05s, validate: 2.5s)')
    def __main__(program, mode, json, out, timeout):
        """Entrypoint for Terminal Capsule."""
        _Registered[mode](program, json, out, timeout=timeout)

    __main__()
