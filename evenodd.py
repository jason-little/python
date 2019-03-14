A = [3,1,2,4]
even = []
odd = []
for i in A:
	if i % 2 == 0 :
		even.append(i)
	else:
		odd.append(i)

print(even + odd)