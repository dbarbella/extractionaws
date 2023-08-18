# Basic utility for revising file names. Shouldn't be necessary under new system, but temporarily preserved 
# for reference.

in_file_handler = open('new_batch_complaints.txt', 'r')
out_file_handler = open('revised_batch_complaints.txt', 'w')

for line in in_file_handler:
    out_file_handler.write('S3:earlham-textract:' + line)
    
    
in_file_handler.close()
out_file_handler.close()