temperatures = [10, -20, -289, 100]

def writer(temperatures):
    with open("temperatures.txt", "w") as file:
        for c in temperatures:
            if c > -273.15:
                f = c* 9/5 +32
                file.write(str(f) + "\n")

writer(temperatures)
