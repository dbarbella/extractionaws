import boto3
import argparse

s3  = boto3.client('s3', region_name='us-east-1')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    
    pdf_addr = args.file
    bucket = pdf_addr.split(':')[1].strip()
    loc_in_bucket = pdf_addr.split(':')[2].strip()
    pdf_id_name = loc_in_bucket.split('/')[-1].strip()
    
    directory = 'fetched_pdfs/'
    
    print(bucket)
    print(loc_in_bucket)
    print(pdf_id_name)
    
    s3.download_file(Filename = directory + pdf_id_name, Key=loc_in_bucket, Bucket=bucket)
    
    ## python3 fetch_file.py "S3:greenfiling-ca:caprod/attachment/2021.01.27/attachment_987335891440457153.pdf"