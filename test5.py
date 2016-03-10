n = int(input("Width of Square = "))
m = int(input("Thickness of Square = "))
print(("*"*n+"\n")*m + ("*"*m+" "*(n-2*m)+"*"*m+"\n")*(n-2*m) + ("*"*n+"\n")*m)


