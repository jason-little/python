import boto3
import hashlib

# Create an S3 client
s3 = boto3.client('s3')

filename = 'file.txt'
bucket_name = 'tr-bastion-pub-keys-374725791127-us-east-1'

s3.upload_file(filename, bucket_name, filename)
s3.put_object_tagging(
    Bucket = bucket_name,
    Key = filename,
    Tagging={
        'TagSet': [
            {
                'Key': 'md5sum',
                'Value': '169fc72bd9befd97f0a6e228d6306a40'
            },
        ]
    }
)

x = s3.get_object_tagging(
    Bucket = bucket_name,
    Key = filename
)

print(x["TagSet"][0]["Value"])

with open(filename,"rb") as f:
    bytes = f.read() # read file as bytes
    readable_hash = hashlib.md5(bytes).hexdigest();
    print(readable_hash)
