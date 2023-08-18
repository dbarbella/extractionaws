import boto3
def get_cont(bucket, filename):
    s3 = boto3.client('s3')
    result = s3.list_objects(Bucket = bucket)
    for file_dict in result.get('Contents'):
        if file_dict.get('Key')==filename:
            data = s3.get_object(Bucket=bucket, Key=filename)
            contents = data['Body'].read()
            print(contents)
def main():
    import argparse
    parser = argparse.ArgumentParser(description='get json contents')
    parser.add_argument('-b','--Bucket', type=str, required=True)
    parser.add_argument('-i','--Filename', type=str, required=True)
    args = parser.parse_args()
    get_cont(args.Bucket, args.Filename)

main()
