import boto3
def get_file_content_s3(bucket):
    s3 = boto3.client('s3')
    BUCKET = bucket
    FOLDER = "complaints_json_output/"
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET, Prefix=FOLDER)
    for page in pages:
        for obj in page['Contents']:
            print(obj.get('Key'))
            
get_file_content_s3("earlham-textract")
