This code was produced as part of a project to extract information from legal documents using AWS services. It was authored by myself and by several students over the course of several years.

Note that the code provided here will not run on its own; several code files and portions of others have been redacted. Some learning code produced by students has also been omitted.

# extractor.py
This program accesses and extracts the following information from processed JSON files, each of which represents one textracted document:
- Amount demanded
- Limited vs. unlimited
- Case type
- Defendant name
- Plaintiff name
- Subcourt
- Document type (complaint, summons, etc.)

This is the standard access point to this part of the system functionality. For each JSON file, it produces a python dictionary (association list).

## How to use

### On the CLI:
* If processing local files: Navigate into the directory containing extractor.py as well as the JSON file you would like to process.
Type ```python3 extractor.py -i file_name.json``` in the terminal.
* If processing remote files from the s3 bucket: Navigate into the directory containing extractor.py.
Type ```python3 extractor.py -b bucket_name -i file_name.json``` in the terminal.

### Below is an example output:

```
attachment_3603094573573261193_analysis_output.json
{'amount': 19913.67, 'case_type': True, 'defendant_name': 'REMOVED', 'plaintiff_name': ': REMOVED', 'input_file': 'attachment_360335454193_analysis_output.json'}

```
### Optional Arguments:

These arguments primarily exist to specify on which files to run. The files must be appropriately-formatted JSON files. The program should generally be run with only one of: -i, -f, -lf. It will work when run with multiple (and produce results for all of them), but this is not the preferred means of running the software and may not be supported in the future.

```-f [inputFiles]``` 
Run on a list of files whose URIs are specified in a file. Currently, these must be files stored on S3; support for local files may be added later. An example of how such a file should be formatted can be found in demo-uris.txt. Results-list files produced by the JSON production portion of the pipeline are automatically formatted appropriately for this.

Example: ```python3 extractor.py -f S3_json_files.txt -d -o testresults001.txt```

```-i [inputFileName]``` 
Run with a single input file, stored locally. The argument is the location of that file. Primarily supported for development and testing.

Example: ```python3 extractor.py -i /home/ubuntu/testing-landing-ground/attachment_1122333081516_analysis_output.json -d -o testresults001.txt```

```-lf [localInputFolder]``` 
Run on all of the json files contained within the specified local folder. Primarily supported for development and testing.

Example: ```python3 extractor.py -lf /home/ubuntu/testing-landing-ground/ -d -o testresults001.txt```

```-o [outputFile]```
Specifies a local file into which to dump the result dictionaries. If not specified, the results will not be stored.

```-d [debug]``` 
Displays additional debug information if true. Defaults to false. Note that if this is not True, the results will not be printed to the terminal.

## Dependencies:

* **json** -- Encoding/decoding json (standard library)
* **os** -- Miscellaneous operating system interfaces (standard library)
* **sys** -- System-specific parameters and functions (standard library)
* **boto3** -- The Amazon Web Services SDK in Python
* **re** -- Regular expressions library (standard library)
* **argparse** -- Parses command line arguments (standard library)

# eval_accuracy.py
This piece of software compares the information we extracted to the canon and produces an accuracy score (percentage of correctly extracted files).

## How to use

### On the CLI:
* Navigate into the directory containing eval_accuracy.py. Open eval_accuracy.py and uncomment one of the four sections at the bottom 
that you would like to process. For example, if you are interested in the amount demanded accuracy, you should uncomment the following: 
```print("check_amount accuracy: ", eval_accuracy('new_batch_complaints.txt', get_amount, check_amount, 'batch2_pdfs_info.json'))```.
Then, in the terminal, type: ```python3 eval_accuracy.py``` and run the command.

### Below is an example output:

```
92.7
```

# get_bucket_contents.py
This program generates a .txt file containing the textracted JSON outputs from the S3 Bucket. 

## How to use

### On the CLI:
* Navigate into the directory containing get_bucket_contents. In the terminal, type: ```python3 get_bucket_contents.py``` and run the command. the .txt file should appear in the same directory. 

# get_file_contents.py
This program retrieves contents from a file located on the S3 Bucket. We use this to run other programs like eval_accuracy.py on remote files.

## How to use

### On the CLI:
* Navigate into the directory containing get_file_contents. In the terminal, type: ```python3 get_file_contents.py -b bucket_name -i json_file_name.json``` and run the command. Contents will appear on the CLI. 

# get_contents.py
This program accesses and returns contents from a specific JSON file on S3.

## How to use

### On the CLI:
* Navigate into the directory containing get_contents.py.
Type ```python3 checklist.py -b bucket_name -i file_name``` in the terminal.

## Dependencies:

* **boto3**

# match_names.py
This program takes two strings as arguments and returns a value between 0 (completely different) and 1000 (identical) indicating how similar they are.

## How to use

* On the CLI: navigate to the drectory containing match_names.py. In the terminal, Type ```match_names.py s1 string1 s2 string2```.

## Dependencies:

* **Collections**
* **string**

# Deprecated Files

We are currently in the process of deprecating the following files. Their functionality has been moved to extractor.py

- extract_subcourt.py
- checklist.py
- distinguish_complaints.py

The following files deal with extracting the name of the attorney that signed the document. For the time being, this functionality has been moved out of scope.

- coordinates.py
- attorneyname.py


# build_json_corpus

## build_json_corpus.py

Built and tested in Python 3.8.5.

**Inputs**
A list of files. These files may be stored locally or on S3. If they are stored locally, they are copied to S3 as part of the processing. See argument inputPdfsLocations below.

**Outputs**
A set of .JSON files. These are produced by feeding the input files through Amazon Textract.

**Dependencies**

Version numbers are the versions with which the code was built and tested. 

**boto3** -- The Amazon Web Services SDK in Python

**json** -- Encoding/decoding json (standard library)

**time** -- Timing library (standard library)

**datetime** -- Timing library (standard library)


### How to use

```python3 build_json_corpus.py [inputPdfsLocations]```

inputPdfsLocations is the (relative or absolute) path to a .txt file that contains a list of URIs to .pdf files. These may be located either on the machine on which you are running or on S3. Files that are located locally will be uploaded to S3 as part of the process. ```pdfs_bucket_addr_in_10.txt``` is an example of such a file.

Paths to local files may resemble this:

```/home/data/samplepdfs3/attachment_2569739892284008779.pdf```

Paths to files on S3 may resemble this:

```S3:greenfiling-ca:caprod/attachment/2021.01.27/attachment_1427725445118988017.pdf```

**Optional arguments**

```-l [localResultsLocation]``` 
Specifies where to store the results locally. If this is left blank, the results will not be stored locally.

```-b [resultsBucket]``` 
Specifies the S3 bucket in which to store the results. If this is left blank, the results will not be stored on S3. The program can store the results in either, neither, or both places.

```-r [resultsURIFile]``` 
Specifies a (local) file location that should be used to store a results URI file. This is a file that contains the URIs of the results produced by the process. This is useful because this file is used by the second part of the pipeline, extraction.

If the results were stored only locally, this will create a file containing local URIs. If the files were stored on S3, it will create a file containing S3 URIs. If they were stored in both places, it will create a file containing S3 URIs. If they were stored nowhere, this file will not be created. This file will automatically overwrite any existing file with the same name.

```--delay [delay]``` 
Sets the time, in seconds, to wait for each file to finish processing. Defaults to 40.

```--debug [debug]``` 
Displays additional debug information if true. Defaults to false.
