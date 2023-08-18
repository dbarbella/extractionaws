import json
import glob
import re
import os

from extractor import get_amount
from extractor import is_limited
from extractor import open_file
from extractor import get_file_content_s3
from extractor import get_party_name_from_complaints
from match_names import *


def get_is_limited(canon_dict, pdf_name):
    if canon_dict[pdf_name]['claimAmount']:
        if float((canon_dict[pdf_name]['claimAmount']).strip("$"))<=25000.0:
            return 'limited'
        else:
            return 'unlimited'

# This isn't actually touching any canon information about whether it's limited or not.
# That's because that doesn't exist in the data.
def check_limited(canon_dict, pdf_name, ext_type):
    if canon_dict[pdf_name]['claimAmount'] and float((canon_dict[pdf_name]['claimAmount']).strip("$"))<=25000.0:
        canon_type_limited = 'limited'
    else:
        canon_type_limited = 'unlimited'
    return canon_type_limited == ext_type


def get_subcourt(canon_dict, pdf_name):
    canon_subcourt = None
    metadata_list = canon_dict[pdf_name]['filingMetadatum']
    for metadata_dict in metadata_list:
        if metadata_dict['name'] == "subCourt":
            canon_subcourt = metadata_dict["value"]
    return canon_subcourt

def check_subcourt(canon_dict, pdf_name, ext_subcourt):
    canon_subcourt = get_subcourt(canon_dict, pdf_name)
    if canon_subcourt is not None and ext_subcourt is not None:
        return canon_subcourt.lower() == ext_subcourt.lower()
        

def get_document_type(canon_dict, pdf_name):
    possible_type = canon_dict[pdf_name]['docTypeApiCode']
    if possible_type != '[TBD]':
        return canon_dict[pdf_name]['docTypeApiCode']

# This is working
def check_document_type(canon_dict, pdf_name, ext_document_type):
    canon_document_type = get_document_type(canon_dict, pdf_name)
    if canon_document_type:
        return canon_document_type.lower() == ext_document_type

def get_amount(canon_dict, pdf_name):
    return canon_dict[pdf_name]['claimAmount']

# This is working
def check_amount(canon_dict, pdf_name, ext_amount):
    canon_amount = get_amount(canon_dict, pdf_name)
    if canon_amount:
        return float((canon_amount).strip("$(),")) == ext_amount

def get_canon_plaintiff(canon_dict, pdf_name):
    name_of_plaintiff = None
    for i in canon_dict[pdf_name]['filingActor']:
        if i['partyRoleApiCode'] == "Plaintiff":
            if i['firstName'] is None and i['middleName'] is None:
                name_of_plaintiff = str(i['lastName'])
            elif i['middleName'] is None:
                name_of_plaintiff = str(i['firstName']) + " " + str(i['lastName'])
            else:
                name_of_plaintiff = str(i['firstName']) + " " + str(i['middleName']) + " " + str(i['lastName'])
    return name_of_plaintiff

def check_plaintiff_complaints(canon_dict, pdf_name, ext_filing_actor):
    name_of_plaintiff = get_canon_plaintiff(canon_dict, pdf_name)
    if name_of_plaintiff and ext_filing_actor is not None:
        accuracy = match_names(name_of_plaintiff, ext_filing_actor)
        if accuracy >= 700:
            # count_correct = count_correct + 1
            name_of_plaintiff = ext_filing_actor

    return name_of_plaintiff == ext_filing_actor

def get_canon_defendant(canon_dict, pdf_name):
    name_of_defendant = None
    for i in canon_dict[pdf_name]['filingActor']:
        if i['partyRoleApiCode'] == "Defendant":
            if i['firstName'] is None and i['middleName'] is None:
                name_of_defendant = str(i['lastName'])
            elif i['middleName'] is None:
                name_of_defendant = str(i['firstName']) + " " + str(i['lastName'])
            else:
                name_of_defendant = str(i['firstName']) + " " + str(i['middleName']) + " " + str(i['lastName'])
    return name_of_defendant
    

def check_defendant_complaints(canon_dict, pdf_name, ext_defendant_actor):
    name_of_defendant = get_canon_defendant(canon_dict, pdf_name)
    if name_of_defendant and ext_defendant_actor is not None:
        accuracy = match_names(name_of_defendant, ext_defendant_actor)
        if accuracy >= 700:
            # count_correct = count_correct + 1
            name_of_defendant = ext_defendant_actor
    return name_of_defendant == ext_defendant_actor

def get_original_uri(file_uri, all_keys):
    search_string = file_uri.split("/")[-1].replace('_detection_output.json', '.pdf')
    # This is wild, but needs to happen because of slashes causing things to be treated
    # as escaped.
    #search_string = search_string[2:]
    for key in all_keys:
        #print(key)
        if search_string in key:
            return key
            
def display_results(total_trials, corrects_dict, both_none_dict, only_extracted_none_dict, only_canon_none_dict, mismatch_dict):
    for key in corrects_dict.keys():
        print("==================")
        print("Results for:", key)
        print("------------------")
        print("Matches: {val} ({percent:.2f}%)".format(val = corrects_dict[key], percent = 100*corrects_dict[key]/total_trials))
        print("Both None: {val} ({percent:.2f}%)".format(val = both_none_dict[key], percent = 100*both_none_dict[key]/total_trials))
        print("Failed to Extract:: {val} ({percent:.2f}%)".format(val = only_extracted_none_dict[key], percent = 100*only_extracted_none_dict[key]/total_trials))
        print("Extracted something where canon has nothing: {val} ({percent:.2f}%)".format(val = only_canon_none_dict[key], percent = 100*only_canon_none_dict[key]/total_trials))
        print("Extracted the wrong thing:: {val} ({percent:.2f}%)".format(val = mismatch_dict[key], percent = 100*mismatch_dict[key]/total_trials))

'''
This is the new and improved version that just uses
the extracted output.
attachment_999169807920760192.pdf
extracted_json is the extracted json file, which is a set of dictionaries
key_types is a list of keys to use, like ['amount']
canon_json is a json file containing canon results.
'''
def eval_accuracy(extracted_json, value_types, canon_json):
    print("Running with extracted data:", extracted_json)
    print("Running with canon file:", canon_json)
    with open(canon_json) as canon_file:
        canon_dict = json.load(canon_file)
    
    both_none_file = open("detailed_eval_results/both_none.txt", "a")
    only_canon_none_file = open("detailed_eval_results/only_canon_none.txt", "a")
    only_extracted_none_file = open("detailed_eval_results/only_extracted_none.txt", "a")
    correct_file = open("detailed_eval_results/correctly_extracted.txt", "a")
    incorrect_file = open("detailed_eval_results/incorrectly_extracted.txt", "a")
    
    # For a given type, this is the function we use to compare to see if two things are equal
    check_functions_for_types = {'amount':check_amount, 'is_limited': check_limited,'plaintiff_name':check_plaintiff_complaints,'defendant_name':check_defendant_complaints, 'document_type':check_document_type, 'subcourt':check_subcourt}
    # For a given type, this is how to get the canon value
    # Do we need both of these, if this information is also baked into check_amount etc.?
    # This one is kind of tricky, because in some cases this isn't stored so overtly
    canon_functions_for_types = {'amount':get_amount,'is_limited': get_is_limited,'plaintiff_name':get_canon_plaintiff,'defendant_name':get_canon_defendant,'document_type':get_document_type, 'subcourt':get_subcourt}
    
    corrects_dict = {}
    both_none_dict = {}
    only_extracted_none_dict = {}
    only_canon_none_dict = {}
    mismatch_dict = {}
    for value_type in value_types:
        corrects_dict[value_type] = 0
        both_none_dict[value_type] = 0
        only_extracted_none_dict[value_type] = 0
        only_canon_none_dict[value_type] = 0
        mismatch_dict[value_type] = 0
    # matched_num = 0
    # both_none_num = 0
    # only_extracted_none_num =0
    # only_canon_none_num = 0
    # mismatch_num = 0
    total_trials = 0
    all_keys = canon_dict.keys()
    with open(extracted_json) as extracted_json_handler:
        for next_dict_line in extracted_json_handler:       
            total_trials += 1
            next_dict_line = next_dict_line.strip()
            # This gets the contents of the processed json file.
            content_dict = json.loads(next_dict_line)
            # ext_output = ext_func(content_dict)
            file_uri = content_dict["file_uri"].strip()
            
            # This is a hardcoded means of getting a .pdf name from the way these files
            # are named in the list file. This is brittle and has to change.
            # Future versions of the code for building corpora will eliminate the need for this.
            pdf_name = get_original_uri(file_uri, all_keys)
            if pdf_name:
                for value_type in value_types:
                    # Get the function that gets the canon value
                    get_canon_func = canon_functions_for_types[value_type]
                    # Get the canon value
                    canon_value = get_canon_func(canon_dict, pdf_name)
                    # Get the extracted value
                    ext_output = content_dict[value_type]
                    # Get the function we use for comparison
                    check_func = check_functions_for_types[value_type]
                    if check_func(canon_dict, pdf_name, ext_output) == True:
                        #matched_num += 1
                        corrects_dict[value_type] = corrects_dict[value_type] + 1
                        correct_file.write("pdf: "+ pdf_name+ " canon: "+ repr(canon_value)+ " extracted: "+ repr(ext_output)+ "\n")
                    elif canon_value == None and (ext_output == None or ext_output == ''):
                        #both_none_num += 1
                        both_none_dict[value_type] = both_none_dict[value_type] + 1
                        both_none_file.write("pdf: "+ pdf_name+ " canon: "+ repr(canon_value)+ " extracted: "+ repr(ext_output)+ "\n")
                    elif canon_value != None and (ext_output == None or ext_output == ''):
                        #only_extracted_none_num += 1
                        only_extracted_none_dict[value_type] = only_extracted_none_dict[value_type] + 1
                        only_extracted_none_file.write("pdf: "+ pdf_name+ " canon: "+ repr(canon_value)+ " extracted: "+ repr(ext_output)+ "\n")
                    elif canon_value == None and ext_output != None:
                        #only_canon_none_num += 1
                        only_canon_none_dict[value_type] = only_canon_none_dict[value_type] + 1
                        only_canon_none_file.write("pdf: "+ pdf_name+ " canon: "+ repr(canon_value)+ " extracted: "+ repr(ext_output)+ "\n")
                    else:
                        #mismatch_num += 1
                        mismatch_dict[value_type] = mismatch_dict[value_type] + 1
                        incorrect_file.write("pdf: "+ pdf_name+ " canon: "+ repr(canon_value)+ " extracted: "+ repr(ext_output)+ "\n")
                '''
                print("filingTypeCode...", canon_dict[pdf_name]['filingTypeCode'], "\n")
                print("court...", canon_dict[pdf_name]['court'], "\n")
                print("filingActor...", canon_dict[pdf_name]['filingActor'], "\n")
                print("attorneyUser...", canon_dict[pdf_name]['attorneyUser'], "\n")
                print("caseType...", canon_dict[pdf_name]['caseType'], "\n")
                print("claimAmount...", canon_dict[pdf_name]['claimAmount'], "\n")
                print("filingMetadatum...", canon_dict[pdf_name]['filingMetadatum'], "\n")
                '''

    both_none_file.close()
    only_canon_none_file.close()
    only_extracted_none_file.close()
    correct_file.close()
    incorrect_file.close()
    accuracy = None
    display_results(total_trials, corrects_dict, both_none_dict, only_extracted_none_dict, only_canon_none_dict, mismatch_dict)
    # correct_num = corrects_dict['plaintiff_name']
    # if total_trials >= 0:
        # accuracy = (correct_num / total_trials)  # accuracy score
    # return accuracy * 100



if __name__ == '__main__':
    eval_accuracy('fix_party_test_1.txt', ['plaintiff_name'], 'batch2_pdfs_info.json')

