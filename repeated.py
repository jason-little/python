A = [2,1,2,5,3,2]
b = set()
for i in A:
	if i in b:
		print(i)
		break
	else:
		b.add(i)

