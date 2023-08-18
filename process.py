import build_json_corpus.build_json_corpus as bjc
import extractor

if __name__ == "__main__":
    import argparse
    
    roleArn = 'removed'
    snsTopicArn = 'removed'
    sqsQueueUrl = 'removed'
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
    
    # This is the location where the extraction process should put the results it produces.
    parser.add_argument('-o', '--outputFile', type = str, required = False)
    
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

    results_uris = bjc.main(**{k: v for k, v in kwargs.items() if v is not None})
    print("results_uris:", results_uris)
    
    content_pairs = extractor.get_results_from_S3_file_list(results_uris)
    extractor.extract_from_content_pairs(content_pairs, debug=True, output_file=args.outputFile)