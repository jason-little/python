#Scaledown

old_max_size = 120
new_max_size = 60

old_desired_capacity = 120
new_desired_capacity = 60

if old_desired_capacity - new_desired_capacity >= 10:
	while old_desired_capacity > new_desired_capacity:
		print(old_desired_capacity)
		old_desired_capacity -= 10

#Scaleup
old_max_size
new_max_size

old_desired_capacity
new_desired_capacity

if  new_desired_capacity - old_desired_capacity >= 10:
	#Scale nicely
	while new_desired_capacity > old_desired_capacity:
		print(new_desired_capacity)
		new_desired_capacity -= 10	
		
