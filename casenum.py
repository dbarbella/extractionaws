import json
import glob
import re
import os

def case_num_dict(canon_json):
    with open(canon_json) as canon_file:
        canon_dict = json.load(canon_file)
    case_dict={}
    #print(canon_dict["S3:greenfiling-ca:caprod/attachment/2021.01.28/attachment_3210891697681526121.pdf"]["courtCase"]["caseNumber"])
    for filing_info in canon_dict:
        try:
            if canon_dict[filing_info]["courtCase"] != None:
                case_number = canon_dict[filing_info]["courtCase"]["caseNumber"]
                doc_type = canon_dict[filing_info]["docTypeApiCode"]
                if case_number in case_dict:
                    (case_dict[case_number]).append([filing_info, doc_type])
                else:
                    case_dict[case_number] = [[filing_info, doc_type]]
        except KeyError:
            continue
    for i in case_dict:
        print(i, case_dict[i])
print(case_num_dict("pdfs_info_canon.json"))
