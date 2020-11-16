import time
old_desired_capacity = 60
new_desired_capacity = 120
scaler = 10
if  new_desired_capacity - old_desired_capacity >= scaler:
        #Scale up nicely
	print("Scaling up nicely in increments of %d" % scaler)
        while new_desired_capacity > old_desired_capacity + scaler:
		old_desired_capacity += scaler
		print("Scaling up to %d instances" % old_desired_capacity)
		time.sleep(3)

old_desired_capacity = 60
new_desired_capacity = 120
if new_desired_capacity - old_desired_capacity >= scaler:
	#Scale down nicely
	print("Scaling down nicely in increments of %d" % scaler)
	while new_desired_capacity > old_desired_capacity + scaler:
		new_desired_capacity -= scaler
		print("scaling down to %d instances" % new_desired_capacity)
		time.sleep(3)
