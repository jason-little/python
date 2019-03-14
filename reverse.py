A = [[1,1,0],[1,0,1],[0,0,0]]
B = []

for i in A:
	C = []
	i = i[::-1]
	for j in i:
		if j == 0:
			C.append(1)
		else:
			C.append(0)
	B.append(C)

print(B)
