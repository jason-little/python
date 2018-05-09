correct_password = "python123"
name = input("Enter your name: ")
surname = input("Enter your surname: ")
password = input("Enter password: ")

while password != correct_password:
    password = input("Wrong password! Enter Again: ")

print("Hi %s %s You are logged in" % (name, surname))
