#--------------------------------------------------------------------------------------

# Textract example code (modified):

import boto3
import json
import time
from datetime import datetime

class ProcessType:
    DETECTION = 1
    ANALYSIS = 2


class DocumentProcessor:
    jobId = ''
    textract = boto3.client('textract')
    sqs = boto3.client('sqs')
    sns = boto3.client('sns')

    roleArn = ''   
    bucket = ''
    document = ''
    
    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''
    
    sleep_timer = 40


    def __init__(self, role, bucket, document, snsTopicArn='', sqsQueueUrl='', region='us-east-1', sleep_timer = 40):    
        self.roleArn = role
        self.bucket = bucket
        self.document = document
        
        self.sleep_timer = sleep_timer

        self.textract = boto3.client('textract', region_name=region)
        self.sqs = boto3.client('sqs', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
        if snsTopicArn and sqsQueueUrl: # if these two parameters are not empty
            self.snsTopicArn = snsTopicArn
            self.sqsQueueUrl = sqsQueueUrl 
        else:
            self.CreateTopicandQueue()   

 
    def ProcessDocument(self,type):
        jobFound = False
        result = None

        self.processType=type
        validType=False

        #Determine which type of processing to perform
        if self.processType==ProcessType.DETECTION:
            response = self.textract.start_document_text_detection(DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                    NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
            print('Processing type: Detection')
            validType=True        

        
        if self.processType==ProcessType.ANALYSIS:
            response = self.textract.start_document_analysis(DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                FeatureTypes=["TABLES", "FORMS"],
                NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})
            print('Processing type: Analysis')
            validType=True    

        if validType==False:
            print("Invalid processing type. Choose Detection or Analysis.")
            return

        print('Start Job Id: ' + response['JobId'])
        dotLine=0
        
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                          MaxNumberOfMessages=10)
            print(f"Number of messages received: {len(response.get('Messages', []))}")
            if sqsResponse:
                #print(sqsResponse)
                time.sleep(self.sleep_timer)
                result = self.GetResults(response['JobId'])
                jobFound = True
                continue
        print('Done!')
        return result
    
    def CreateTopicandQueue(self):
      
        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic
        snsTopicName="AmazonTextractTopic" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        #create SQS queue
        sqsQueueName="AmazonTextractQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']
 
        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                    AttributeNames=['QueueArn'])['Attributes']
                                        
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue 
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqsQueueArn, self.snsTopicArn)
 
        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

    #Display information about a block
    def DisplayBlockInfo(self,block):
        
        print ("Block Id: " + block['Id'])
        print ("Type: " + block['BlockType'])
        if 'EntityTypes' in block:
            print('EntityTypes: {}'.format(block['EntityTypes']))

        if 'Text' in block:
            print("Text: " + block['Text'])

        if block['BlockType'] != 'PAGE':
            print("Confidence: " + "{:.2f}".format(block['Confidence']) + "%")

        print('Page: {}'.format(block['Page']))

        if block['BlockType'] == 'CELL':
            print('Cell Information')
            print('\tColumn: {} '.format(block['ColumnIndex']))
            print('\tRow: {}'.format(block['RowIndex']))
            print('\tColumn span: {} '.format(block['ColumnSpan']))
            print('\tRow span: {}'.format(block['RowSpan']))

            if 'Relationships' in block:
                print('\tRelationships: {}'.format(block['Relationships']))
    
        print('Geometry')
        print('\tBounding Box: {}'.format(block['Geometry']['BoundingBox']))
        print('\tPolygon: {}'.format(block['Geometry']['Polygon']))
        
        if block['BlockType'] == 'SELECTION_ELEMENT':
            print('    Selection element detected: ', end='')
            if block['SelectionStatus'] =='SELECTED':
                print('Selected')
            else:
                print('Not selected')  


    def GetResults(self, jobId):
        maxResults = 1000
        paginationToken = None
        finished = False

        complete_result = {}
        token_ct = 1

        while finished == False:

            response=None

            if self.processType==ProcessType.ANALYSIS:
                if paginationToken==None:
                    response = self.textract.get_document_analysis(JobId=jobId,
                        MaxResults=maxResults)
                else: 
                    response = self.textract.get_document_analysis(JobId=jobId,
                        MaxResults=maxResults,
                        NextToken=paginationToken)                           

            if self.processType==ProcessType.DETECTION:
                if paginationToken==None:
                    response = self.textract.get_document_text_detection(JobId=jobId,
                        MaxResults=maxResults)
                else: 
                    response = self.textract.get_document_text_detection(JobId=jobId,
                        MaxResults=maxResults,
                        NextToken=paginationToken)   

            complete_result['Token{}'.format(token_ct)] = response

            if 'NextToken' in response:
                paginationToken = response['NextToken']
                token_ct += 1
            else:
                finished = True

        return complete_result


    def GetResultsDocumentAnalysis(self, jobId):
        maxResults = 1000
        paginationToken = None
        finished = False

        while finished == False:

            response=None
            if paginationToken==None:
                response = self.textract.get_document_analysis(JobId=jobId,
                                            MaxResults=maxResults)
            else: 
                response = self.textract.get_document_analysis(JobId=jobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken)  
            
            #Get the text blocks
            blocks=response['Blocks']
            print ('Analyzed Document Text')
            print ('Pages: {}'.format(response['DocumentMetadata']['Pages']))
            # Display block information
            for block in blocks:
                self.DisplayBlockInfo(block)
                print()
                print()

                if 'NextToken' in response:
                    paginationToken = response['NextToken']
                else:
                    finished = True


#--------------------------------------------------------------------------------------
import logging
import os
from botocore.exceptions import ClientError


def create_S3_bucket(bucket_name, region='us-east-2'):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-2).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_file_to_S3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    
    print("Attempting to upload file:", file_name)

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except boto3.exceptions.S3UploadFailedError as e:
        if 'NoSuchBucket' in str(e): 
        # if the error is because there is no bucket with the given name
            create_S3_bucket(bucket)
            response = s3_client.upload_file(file_name, bucket, object_name)
        else:
            logging.error(e)
            return False
    except ClientError as e:
        logging.error(e)
        return False

    return True

def is_S3_URI(location):
    if (len(location) >= 3 and location[0:3] == "S3:"):
        return True
    else:
        return False
        
def is_comment(location):
    if (len(location) >= 1 and location[0] == "#"):
        return True
    else:
        return False
    
  
def lift_local_files_to_S3(input_pdfs_file,
                           S3_uri_file='',
                           pdf_to_bucket='',
                           overwrite=False,
                           debug=True):
    """When running with files that are stored locally, they need to first be
    moved to S3. This function works with a .txt file that contains a list of
    files. Any that are stored locally will be lifted to S3.
    
    This function does not directly invoke textract at all; it is used for
    moving local files to S3, to allow them to be processed with the same
    pipeline used to process files already stored there.

    Parameters:
    
    input_pdfs_file (str): The relative or absolute location of
    a .txt file that contains a list of .pdf file locations, one per line.
    If a relative path is given, it is converted to an absolute path.
    This file may contain both local files and files on S3.
    
    S3_uri_file (str): The name of the file that will be populated with the S3
    URIs. Note that this will overwrite the old file if the same file name is used more than once.
    If this argument is not provided, then it will be automatically generated.
    The automatically generated name includes the current date and time.
    
    pdf_to_bucket (str): The name of the bucket to use. If none is provided, one
    will be generated with the same date and time used to generate S3_uri_file.
    
    :return: 
    """
    
    # If none of the files are local files, we don't need to do any lifting.
    local_files_found = False
    
    now = datetime.now()
    
    # relative_path = '../setup/complaint_pdf_corpus_219.txt'
    input_pdfs_file_abs_location = os.path.abspath(input_pdfs_file)
    pdfs_list_handler = open(input_pdfs_file_abs_location, "r")

    # These are all of the files we need to process.
    lines_to_process = pdfs_list_handler.readlines()
    # If every line is an S3 location or a comment, we're finished.
    if all((is_comment(element) or is_S3_URI(element)) for element in lines_to_process):
        if (debug):
            print("All provided locations are S3 URIs. No lifting necessary.")
        return input_pdfs_file

    # If we got here, there's at least one line that's not a comment or a
    # S3 URI.
    if not S3_uri_file:
        # Here we autogenerate a file name.
        # Technically this can clobber if more than one is generated
        # per second.
        S3_uri_file = os.path.abspath('./S3_uris_' + now.strftime("%Y-%m-%d-%H%M%S"))
    
    S3_uri_file_handler = open(S3_uri_file, "w")

    if not pdf_to_bucket:
        # pdf_to_bucket = 'extracted_json_' + now.strftime("%Y-%m-%d-%H%M%S")
        pdf_to_bucket = 'earlham-textract'
    
    # upload all the local pdfs stored in pdfs_local_addr to the bucket specified above:
    for pdf_addr in lines_to_process:
        print("Processing:", pdf_addr)
        # This needs to detect whether a line is a local file, an S3 file,
        # a comment, or garbage.
        # S3 locations start with S3:
        # Comments start with #
        # S3 location and comments don't need to be lifted.
        if (is_comment(pdf_addr) or is_S3_URI(pdf_addr)):
            S3_uri_file_handler.write(pdf_addr)
        else:
            pdf_name = os.path.basename(pdf_addr).strip()
            pdf_dir = os.path.dirname(pdf_addr).strip()
            pdf_addr_stripped = pdf_addr.strip()

            # specify the location of the pdf inside the bucket below:
            # e.g. /folder/subfolder/pdf_name.pdf
            # This needs some additional polish/figuring out, but should at least work.
            object_name = 'apitest/{}'.format(pdf_name) 

            # upload the pdf to S3:
            upload_file_to_S3(pdf_addr_stripped, pdf_to_bucket, object_name)

            # write the bucket address pdfs_bucket_addr_in:
            S3_uri_file_handler.write('S3:{}:{}\n'.format(pdf_to_bucket, object_name))

    pdfs_list_handler.close()
    S3_uri_file_handler.close()    
    return S3_uri_file

# input_pdfs_local_location is the path to a file that is just a plaintext
# list of the local locations of a set of .pdf files, one per line.
# ../setup/complaint_pdf_corpus_219.txt is an example
def main(roleArn, snsTopicArn, sqsQueueUrl, region,
         input_pdfs_locations,
         local_results_location = '',
         results_bucket = '',
         sleep_timer = 40, 
         debug = False,
         json_to_bucket = 'earlham-textract',
         results_uri_file = None):
    
    results_prefix = "sept_test_10k_0001"
    results_uris = []
    
    if (not local_results_location and not results_bucket):
        print("Both localResultsLocation and resultsBucket were left unspecified; \
               results will be computed, but not stored.")
    
    # This can be extended to fine-tune the behavior later if need be.
    input_pdfs_S3_location = lift_local_files_to_S3(input_pdfs_locations)
    pdfs_bucket_addr_in = os.path.abspath(input_pdfs_S3_location)

    if local_results_location and os.path.isdir(local_results_location)==False:
         os.mkdir(local_results_location)
         
    s3 = boto3.resource('s3')

    if results_uri_file:
        results_uri_file_handler = open(results_uri_file, 'w')

    with open(pdfs_bucket_addr_in, 'r') as bucket_pdfs_list:

        for pdf_addr in bucket_pdfs_list:
            print("\n-------Starting next job-------")
            print("PDF Address:")
            print(pdf_addr)
            bucket = pdf_addr.split(':')[1].strip()
            loc_in_bucket = pdf_addr.split(':')[2].strip()
            pdf_id_name = loc_in_bucket.split('/')[-1].strip()
            

            # run Textract on the pdf:
            analyzer = DocumentProcessor(roleArn, bucket, loc_in_bucket, snsTopicArn, sqsQueueUrl, region, sleep_timer = sleep_timer)
            #result = analyzer.ProcessDocument(ProcessType.ANALYSIS)
            result = analyzer.ProcessDocument(ProcessType.DETECTION)
            
            print("results_uri_file:", results_uri_file)
            print("results_bucket:", results_bucket)
            
            if local_results_location:
            # output to local directory:
                if debug:
                    print ("Outputting to local directory: " + local_results_location)
                # os.chdir(local_results_location) # cd to the output dir
                # put the result into a json file:
                next_file_name = '{}_analysis_output.json'.format(pdf_id_name.rstrip('.pdf'))
                next_file_uri = local_results_location + next_file_name
                with open(next_file_uri, 'w') as json_file:
                   json.dump(result, json_file, indent=4)
                print("Geting here")
                if not results_bucket:
                    results_uris.append(next_file_uri)
                    if results_uri_file:
                        print("Writing...")
                        results_uri_file_handler.write(next_file_uri + "\n")
            
            if results_bucket:
                # output to S3 bucket:
                if debug:
                    print ("Outputting to S3 Bucket: " + results_bucket)
                next_file_name = results_prefix + "/" + '{}_detection_output.json'.format(pdf_id_name.rstrip('.pdf'))
                json_s3_obj = s3.Object(json_to_bucket, next_file_name)
                json_s3_obj.put(Body=json.dumps(result, indent = 4))
                next_file_uri = 'S3:{}:{}'.format(results_bucket, next_file_name)
                results_uris.append(next_file_uri)
                if results_uri_file:
                    print("Writing...")
                    #results_uri_file_handler.write(next_file_name + "\n")
                    results_uri_file_handler.write(next_file_uri + '\n')
                    
    
    if results_uri_file:
        results_uri_file_handler.close()
    
    return results_uris

 
if __name__ == "__main__":
    import argparse
    
    roleArn = 'arn:aws:iam::368219584212:role/earlham_textract'
    snsTopicArn = 'arn:aws:sns:us-east-1:368219584212:AmazonTextractBuild_json_corpus_test'
    sqsQueueUrl = 'https://sqs.us-east-1.amazonaws.com/368219584212/build_json_corpus_test_queue'
    region ='us-east-1'
    
 
    parser = argparse.ArgumentParser(description='checklist')
    # The location to store the data locally. If this isn't included, the
    # data will be stored on S3 in a default location.
    parser.add_argument('inputPdfsLocations', type = str)
    parser.add_argument('-l','--localResultsLocation', type = str, required = False)
    parser.add_argument('-b','--resultsBucket', type = str, required = False)
    
    # A location for a file that contains a list of the results files. Prioritizes S3
    # if results files have been stored both locally and on S3. Does nothing if results
    # have not been stored.
    parser.add_argument('-r','--resultsURIFile', type = str, required = False)
    parser.add_argument('--delay', type = int, required = False)
    parser.add_argument('--debug', required = False, action='store_true')
    
    args = parser.parse_args()

    kwargs = dict(roleArn=roleArn,
                  snsTopicArn=snsTopicArn,
                  sqsQueueUrl=sqsQueueUrl,
                  region=region,
                  input_pdfs_locations = args.inputPdfsLocations,
                  local_results_location = args.localResultsLocation,
                  results_bucket = args.resultsBucket,
                  sleep_timer = args.delay,
                  debug = args.debug,
                  results_uri_file = args.resultsURIFile
                  )

    main(**{k: v for k, v in kwargs.items() if v is not None})
    import timeit
#     print("\nTotal time taken: ", timeit.timeit(main, number=1))
