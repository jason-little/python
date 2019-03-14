import requests
import os
import random
import string
import json

chars = string.ascii_letters + string.digits + '!@#$%^&*()'
random.seed = (os.urandom(1024))

url = 'http://www.google.ca'

names = json.loads(open('names.json').read())

for name in names:
  name_extra = ''.join(random.choice(string.digits))

  username = name.lower() + name_extra + '@yahoo.com'
  password = ''.join(random.choice(chars) for i in range(8))


  #requests.post(url, allow_redirects=False, data = {
  #  'df3f33e3fff44': username,
  #  'ioh3orhi3hi3u': password
  #})

  print 'sending username %s amd password %s' % (username, password)
