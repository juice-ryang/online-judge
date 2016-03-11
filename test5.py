import time
n = int(input("Width of Square = "))
time.sleep(.5)
m = int(input("Thickness of Square = "))
time.sleep(.5)
print(("*"*n+"\n")*m + ("*"*m+" "*(n-2*m)+"*"*m+"\n")*(n-2*m) + ("*"*n+"\n")*m)


