import json
import sys
import os.path
import boto3

def get_cont(bucket, filename):
    s3 = boto3.client('s3')
    result = s3.list_objects(Bucket = bucket)
    for file_dict in result.get('Contents'):
        if file_dict.get('Key')==filename:
            data = s3.get_object(Bucket=bucket, Key=filename)
            contents = data['Body'].read().decode('utf-8')
            return contents

def open_file(filename):
    print("Opening file in checklist.py for some reason:", filename)
    with open(filename) as json_file:
        content=json.load(json_file)
    print("~~~~~content~~~~~")
    #print(content)
    blocks=content['Token1']["Blocks"]
    return blocks

def get_attorney(file_blocks): #returns the name of the attorney
    info=""
    user=""
    check=""
    name=[]
    newstr=""
    long=[]
    long1=0
    check2=0
    information=""
    
    i=0
    while file_blocks[i]["Page"]<=1:#searches for name of the attorney on the top of the document
        i+=1
        try:
            if file_blocks[i]["Text"].lower().startswith("superior"):
            	
                break
            info+=file_blocks[i]["Text"]
            info+="\n"
        except KeyError:
                continue
    
    for i in info:
    	if not i.isdigit():
    		check+=i
    		         
    for i in check.split("\n"):#uses the name on top of the document to locate the same names on other pages
    	
    	if "State" or "SB" in i:
    		
    		user+=i
    		newstr=user.replace('State Bar No.:', '')
    		
    for block in file_blocks:#finds coordinates of the names
        try:
            if block["Text"] in newstr:
            	if len(block["Text"]) >=3:
                	name.append(block['Geometry']['Polygon'])
            	
        except KeyError:
            continue	
           
    store=get_cordinates(file_blocks)#Coordinates of the Selected checkboxes
 	
    #print(user)

    for i in name:
    	long.append(i[0]['Y'])   
    for i in store:
    	long1+=i[0]['Y']
    	
    check2=min(long, key=lambda x:abs(x-long1))	#finds the closest point using coordinates of the checked checkbox
    
    for block in file_blocks:#returns name using those points
        try:
        	for i in block['Geometry']['Polygon']:
        		
        		if check2==i['Y']:
        			
        			print(block["Text"])
        			break

            	
        except KeyError:
            continue
    		
    	
'''
The status of this file is unclear; it looks like some of its functionality has been
migrated to extractor.py.
'''
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='checklist')
    parser.add_argument('-i','--inputFileName', type=str, required = True)
    parser.add_argument('-b','--Bucket', type=str, required = False)
    args = parser.parse_args()
    if args.Bucket:
        content = get_cont(args.Bucket, args.inputFileName)
        json_content = json.loads(content)
        blocks=[]
        tokens=len(json_content)
        #print(tokens)
        for token in range(1,tokens+1):
            for block in json_content["Token{}".format(token)]["Blocks"]:
                blocks.append(block)
    else:
        if not(os.path.isfile(args.inputFileName)):
            print("error,", args.inputFileName, "does not exist", file=sys.stderr)
            exit(-1)
        blocks=open_file(args.inputFileName)
    #print("amount = ", get_amount(blocks))
    #print("is limited = ", get_type(blocks))
    #print("Attorneys: ")
    #print(get_attorney_info(blocks))
    #python3 checklist.py -i Attach_6187349_analysis_output.json
