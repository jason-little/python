moves = "UDD"
x = 0
y = 0

for i in moves:
	if i == "U":
		x += 1
	elif i == "D":
		x -= 1
	elif i == "R":
		y += 1
	else:
		y -= 1
if x == 0 and y == 0:
	print("True")
else:
	print("False")