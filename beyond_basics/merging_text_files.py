import datetime
import glob2

myfile = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f.txt")
filenames = glob2.glob('file*.txt')
with open(myfile, 'w') as file:
    for filename in filenames:
        with open(filename, 'r') as f:
            file.write(f.read() + "\n") 
