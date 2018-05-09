from datetime import datetime
delta = datetime.now() - datetime(1900, 12, 31)
print(delta.seconds, delta.days, datetime.now())
