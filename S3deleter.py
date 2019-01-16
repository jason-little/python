
import boto3
s3 = boto3.resource("s3")

file = open("GAP2.csv", "r")
for i in file.readlines():
  bucket = s3.Bucket("gap-vps-logs-prod")
  if i.strip():
  objects = bucket.objects.filter(Prefix="%s" % i.rstrip('\r\n'))
  objects.delete() 

  else:
    print("blank line")
