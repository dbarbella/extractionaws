'''
Simple tool for building a list of random files
for which we have gold standard information.
'''

import json
import random
import build_json_corpus.build_json_corpus as bjc

def build_corpus(canon_json, size, output_location):
    with open(canon_json) as canon_file:
        canon_dict = json.load(canon_file)
        keys = canon_dict.keys()
        keys_list = list(keys)
        print(len(keys_list))
        sample = random.sample(keys_list, size)
        with open(output_location, 'w') as output_file:
            for element in sample:
                output_file.write(element + '\n')

if __name__ == "__main__":
    build_corpus('batch2_pdfs_info.json', 10443, 'sept_corpus_list_10k.txt')