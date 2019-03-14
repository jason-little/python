class Person:

	name = None
	age = None

	def __init__(self, name, age):
		self.name = name
		self.age = age

	def say_name(self):
		print 'My name is %s' % self.name

	def say_age(self):
		print 'My age is %s' % self.age