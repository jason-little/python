correct_password = "python123"
password = input("Enter password: ")

while password != correct_password:
    password = input("Wrong password! Enter Again: ")

print("Logged in")
