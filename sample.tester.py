from process_capsule import PythonCapsule as PC
from process_capsule import prompt_spliter as P

with open("sample.real.out", "wb") as log:
    with PC("sample.py", logfile=log) as process:
        process.run(with_check=False)
        try:
            for i in open("sample.in").read().split():
                process.write(i)[1]
        except PC.DEAD as e:
            pass
