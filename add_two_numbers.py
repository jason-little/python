
class Node:
    def __init__(self,val):
        self.val = val
        self.next = None # the pointer initially points to nothing

l1 = Node(2)
l1.next = Node(4)
l1.next.next = Node(3)
a = ""

l2 = Node(5)
l2.next = Node(6)
l2.next.next = Node(4)
b = ""
c = ""

while l1 is not None:
	a = a + str((l1.val))	
	l1 = l1.next

while l2 is not None:
	b = b + str((l2.val))	
	l2 = l2.next

sum = int(a[::-1]) + int(b[::-1])

firstvalue = 'yes'

for i in str(sum)[::-1]:
    if firstvalue == 'yes':
        l3.add_node(i)
    else:
        l3 = l3.next
        l3.add_node(i)
