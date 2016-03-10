from process_capsule import PythonCapsule as PC

print('test1')
with open("test.log", "wb") as log:
    process = PC('test2.py', logfile=log)
    try:
        print('-run')
        print(process.run(with_check=True))
        print('-write')
        print(process.write("helloworld", True))
        print('-read')
        print(process.read())
    except PC.DEAD as e:
        print('dead')
        print((e.__str__()))

input()

print('test2')
with open("test2.log", "wb") as log:
    with PC('test2.py', logfile=log) as process:
        try:
            print('-run')
            print(process.run(with_check=True))
            print('-write')
            print(process.write("helloworld", True))
            print('-read')
            print(process.read())
        except PC.DEAD as e:
            print('dead')
            print((e.__str__()))

input()
