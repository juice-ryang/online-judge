from OnlineJudgeServer.terminal_capsule import _Registered


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
