from process_capsule import PythonCapsule as PC
from process_capsule import prompt_spliter as P

with open("test5.log", "wb") as log:
    with PC("test5.py", logfile=log) as process:
        with open("test5.out", "w") as out:
            process.run(with_check=False)
            try:
                for i in open("in").read().split():
                    out.write(process.write(i)[1])
            except PC.DEAD as e:
                print('DEAD!!!!!!!!!!!!!!')
                print(str(e))
