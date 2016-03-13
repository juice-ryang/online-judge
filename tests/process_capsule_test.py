from process_capsule import PythonCapsule as PC

print('test1')
process = PC('process_capsule_test_target.py', logfile=None)
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
with PC('process_capsule_test_target.py', logfile=None) as process:
    try:
        print('-run')
        print(process.run(with_check=True))
        print('-write')
        print(process.write("helloworld", True))
        print('-read')
        print(process.read())
        print(process.write("helloworld,too"))
    except PC.DEAD as e:
        print('dead')
        print((e.__str__()))

input()
