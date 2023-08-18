import boto3

#S3:earlham-textract:attachment_6710200704172666400_analysis_output.json
def all_files_in_bucket(bucket_name, subbucket, output_file):
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    output_handler = open(output_file, 'w')
    print(bucket.objects.all())
    total = 0
    for i in bucket.objects.filter(Prefix=subbucket):
        total += 1
        next_string = "S3:" + i.bucket_name + ":" + i.key + '\n'
        print(next_string, end = '')
        output_handler.write(next_string)
    print(total)
    output_handler.close()
    
    
all_files_in_bucket('earlham-textract', 'sept_test_10k_0001', 'sept_corpus_bucket_list_10k.txt')