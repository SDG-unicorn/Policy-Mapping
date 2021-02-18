import io, csv, re, os, json
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
from whoosh.lang.porter import stem
import xlsxwriter
from itertools import chain
##MM imports
import datetime as dt
import pathlib
import logging
import time

from docx2python import docx2python
 
from polmap.polmap import make_directories, preprocess_text, doc2text # replaced the keyword processing block


######################################
########### 1) Define global variables like time, input_dir, ouput_dirs
print('Begin text mapping.\n')
start_time = time.time()

input_dir = pathlib.Path.cwd() / 'pdf_re' / 'SA_and_Kenya_TEI' #'Test' / 'Eurlex' #MM let user provide an input dir
input_folder_name = input_dir.name

## 1.a) Create output folder structure based on input name, date and time of exectution

output_dir_dict = make_directories(input_dir) #Set exist_ok=False later on

project_title=output_dir_dict['out_dir'].name

out_dir, log_dir, results_dir, doctext_dir, doctext_stemmed_dir, processed_keywords_dir, keyword_count_dir = output_dir_dict.values()

for key, value in output_dir_dict.items():
    if output_dir_dict[key].exists() and output_dir_dict[key].is_dir():
        print(key+' succesfully created in:\n'+'{}\n'.format(str(value)))

print('Output folder is: \n'+str(output_dir_dict['out_dir'])+'\n')

## 1.b) Read all files in input directory and select allowed filetypes

allowed_filetypes =  ['.pdf','.html','.mhtml','.doc','.docx'] # ['.doc','.docx'] # 

files = sorted(input_dir.glob('**/*.*'))
files = [ file for file in files if file.suffix in allowed_filetypes]

policy_documents = pd.DataFrame(files, columns=['Input_files'])
policy_documents.index = policy_documents.index + 1
policy_documents['Paths']=policy_documents['Input_files'].apply(lambda doc_path: pathlib.PurePath(*doc_path.parts[doc_path.parts.index(input_dir.name)+1:]))

policy_documents['Paths'].to_csv(results_dir.joinpath('file_list.txt'), sep='\t', encoding='utf-8')

## 1.c) Create logfile for current run.

log_file = log_dir / 'mapping_{}.log'.format(project_title)
log_file.touch(mode=0o666)
logging.basicConfig(filename=log_file, filemode='a', level=logging.WARNING)

with open(log_file, 'a') as f:
    f.write( 
        '1) Creating folders, reading input folder and listing all file paths : {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

print('Step 1: Listed paths of documents and created main output folders.\n')


######################################
########### 2) MM Read the list of keywords and apply the prepare_keyords text processing function from polmap
start_time = time.time()

keywords_excel = 'keys_update_27012020.xlsx'

#keywords_sheets= [Targ]

keys = pd.read_excel(keywords_excel, sheet_name= 'Target_keys' ) #MM 'keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'Sheet1' 
goal_keys = pd.read_excel(keywords_excel, sheet_name= 'Goal_keys' ) #MM Create a dictionary of dataframes for each sheet
dev_count_keys = pd.read_excel(keywords_excel, sheet_name= 'MOI' ) #MM 'keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'Sheet2' 


#remove all from stop_words to keep in keywords
stop_words = set(stopwords.words('english'))
stop_words.remove('all')

keys['Keys']=keys['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))
goal_keys['Keys']=goal_keys['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))
dev_count_keys['Keys']=dev_count_keys['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))

keys['Keys']=keys['Keys'].apply(lambda keywords: [preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])
goal_keys['Keys']=goal_keys['Keys'].apply(lambda keywords: [preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])
dev_count_keys['Keys']=dev_count_keys['Keys'].apply(lambda keywords: [preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])

##Country names
countries_in = pd.read_excel(keywords_excel, sheet_name= 'developing_countries') #MM 'keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'developing_countries'
countries = countries_in['Name'].values.tolist()
country_ls = []
for element in countries:
    element = [re.sub(r'[^a-zA-Z-]+', '', t.lower().strip()) for t in element.split()]
    # countries = [x.strip(' ') for x in countries]
    element = [stem(word) for word in element if not word in stop_words]
    element = ' '.join(element)
    country_ls.append(element)

keywords_filename = processed_keywords_dir / 'processed_keywords.xlsx'
keywords_filename = pd.ExcelWriter(keywords_filename, engine='openpyxl')
keys.to_excel(keywords_filename, sheet_name='Targets_kwrds')
goal_keys.to_excel(keywords_filename, sheet_name='Goal_kwrds')
dev_count_keys.to_excel(keywords_filename, sheet_name='MOI_kwrds')
pd.DataFrame(country_ls,columns=['Name']).to_excel(keywords_filename, sheet_name='dev_countries_kwrds')
keywords_filename.save()

with open(log_file, 'a') as f:
    f.write( 
        '2) Reading and preprocessing keywords: {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

print('Step 2: Read and processed keywords.\n')


######################################
########### 3) Read document files and convert them into text
start_time = time.time()

PDFtext = [] #This can easily become a dictionary with filepath as a key and text as a value
counter = 0
for file_path in files:
    counter += 1
    try:
        doc_text = doc2text(file_path)
       # while '\n\n\n\n' in doc_text : doc_text = doc_text.replace('\n\n\n\n', '\n\n\n') #docx2python specific fix. would probably fit better elsewhere
        textfile_dest_ = file_path.parts[file_path.parts.index(input_dir.name)+1:]
        textfile_dest =  doctext_dir.joinpath(*textfile_dest_)
        textfile_dest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        textfile_dest = textfile_dest.parent / str(textfile_dest.name.replace('.','_')+'.txt')
        with open(textfile_dest, 'w', encoding='utf-8') as file_:
           file_.write(doc_text)
        PDFtext.append(['/'.join(textfile_dest_),doc_text])
    except Exception as excptn: #MM I'd log errors as described in https://realpython.com/python-logging/, we need to test this.
        print(excptn)
        logging.exception('{doc_file} raised exception: {exception} \n\n'.format(doc_file=file_path.name, exception=excptn))



with open(log_file, 'a') as f:
    f.write( 
        '3) Reading, converting and saving {docs} documents as text: {seconds:.3e} seconds\n\n'.format(docs=len(PDFtext),seconds=(time.time()-start_time))
    )

print('Step 3: Converted {docs} documents to text.\n'.format(docs=len(PDFtext)))


######################################
########### 4) Read document files and convert them into text
start_time = time.time()

for item in PDFtext:
    #detect soft hyphen that separates words
    item[1] = item[1].replace('. ', ' . ') # item[1] = re.sub(r'([a-z])([-:,;])(\s)', r'\1 \2\3', item[1])
    item[1] = re.sub(r'-\n', '', item[1])
    #item[1] = re.sub(r'(\w+)\n(\w+)', r'\1 \2', item[1]) #remove line returns between words
    # item[1] = [re.sub(r'-\n', '', t) for t in item[1].split()]
    # #get indices of soft hyphens
    # indices = [i for i, s in enumerate(item[1]) if '\xad' in s]
    # #merge the separated words
    # for index in indices:
    #     item[1][index] = item[1][index].replace('\xad', '')
    #     item[1][index+1] = item[1][index]+item[1][index+1]
    # #remove unnecessary list elements
    # for index in sorted(indices, reverse=True):
    #     del item[1][index]
    item[1] = preprocess_text(item[1], stop_words)
    #item[1] = item[1].replace(' . ', ' . \n')
    #save out
    item_path = doctext_stemmed_dir / pathlib.PurePath(item[0]) #stemmed_doctext_dir / pathlib.PurePath(item[0])
    item_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    item_path = item_path.parent / (item_path.name.replace('.','_')+'_stemmed.txt')

    with open(item_path, 'w', encoding='utf-8') as stemdoctext:
           stemdoctext.write(item[1]+'\n\nTextlenght: {}'.format(len(item[1])))
    #Append textlenght
    item = item.append(len(item[1])) #MM @


with open(log_file, 'a') as f:
    f.write( 
        '4) Processing and stemming text of {docs} documents: {seconds:.3e} seconds\n\n5) Counting of keywords in text:\n\n'.format(docs=len(PDFtext),seconds=(time.time()-start_time))
    )

print('Step 4: Processed and stemmed text from {docs} documents.\n'.format(docs=len(PDFtext)))


######################################
########### 5) Counting keywords within text
start_count_time = time.time()
start_time = time.time()

## 5.1) Count Target keywords

target_col_names=['Policy', 'Target', 'Keyword', 'Count', 'Textlength']

target_ls = []
count_file_dict={}
##make the count
for item in PDFtext:
    doc_target_ls =[]
    targetcount_filedest = keyword_count_dir / pathlib.PurePath(item[0])
    targetcount_filedest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    targetcount_filedest = targetcount_filedest.parent / (targetcount_filedest.name.replace('.','_')+'.xlsx')
    count_file_dict[item[0]]=targetcount_filedest
    with pd.ExcelWriter(targetcount_filedest, mode='w', engine='openpyxl') as destfile: #replace with xlsx writer, make full target ls per document and save it
        for i in range(0, len(keys['Keys'])):
            for j in range(0,len(keys['Keys'][i])):
                # print(keys['Keys'][i][j])
                counter = item[1].count(str(keys['Keys'][i][j]))
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                if counter > 0:
                    row=[item[0], keys['Target'][i], keys['Keys'][i][j], counter, len(item[1])]
                    target_ls.append(row)
                    doc_target_ls.append(row)
                    #dfObj = dfObj.append(pd.Series(target_ls[-1], index=target_col_names), ignore_index=True)
                else:
                    continue
        dfObj= pd.DataFrame(doc_target_ls, columns=target_col_names)
        dfObj.to_excel(destfile, sheet_name='Target_raw_count')
    

target_df = pd.DataFrame(target_ls, columns=target_col_names)

#drop rows where keyword = ''
# print(len(final_df['Target']))
target_df = target_df[target_df.Keyword != '']
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
target_df = target_df[target_df.Count != 0]
# print(len(final_df['Target']))

# Create a Pandas Excel writer using XlsxWriter as the engine.

write_name = results_dir / 'mapping_{}.xlsx'.format(project_title)
writer = pd.ExcelWriter(write_name, engine='openpyxl')

print('Final results are stored in:\n{}\n'.format(write_name))

#export final output
target_df.to_excel(writer, sheet_name='Target_raw_count')
#writer.save()

with open(log_file, 'a') as f:
    f.write( 
        '- 5.1) Counting target keywords in texts: {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

## 5.2) Count Goals keywords
start_time = time.time()

goal_col_names=['Policy', 'Goal', 'Keyword', 'Count', 'Textlength']

goal_ls = []
##make the count
for item in PDFtext:
    goal_doc_ls=[]
    with pd.ExcelWriter(count_file_dict[item[0]], mode='a', engine='openpyxl') as destfile:
        for i in range(0, len(goal_keys['Keys'])):
            for j in range(0,len(goal_keys['Keys'][i])):
                # print(keys['Keys'][i][j])
                counter = item[1].count(str(goal_keys['Keys'][i][j]))
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                if counter > 0:
                    row=[item[0], goal_keys['Goal'][i], goal_keys['Keys'][i][j], counter, len(item[1])]
                    goal_ls.append(row)
                    goal_doc_ls.append(row)
                    #dfObj = dfObj.append(pd.Series(goal_ls[-1], index=goal_col_names), ignore_index=True)
                else:
                    continue
        dfObj = pd.DataFrame(goal_doc_ls, columns=goal_col_names)
        dfObj.to_excel(destfile, sheet_name='Goal_raw_count')
                

goal_df = pd.DataFrame(goal_ls, columns=goal_col_names)

#drop rows where keyword = ''
# print(len(final_df['Target']))
goal_df= goal_df[goal_df.Keyword != '']
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
goal_df = goal_df[goal_df.Count != 0]
# print(len(final_df['Target']))

# Create a Pandas Excel writer using XlsxWriter as the engine.

#export final output
goal_df.to_excel(writer, sheet_name='Goal_raw_count')

with open(log_file, 'a') as f:
    f.write( 
        '- 5.2) Counting goal keywords in texts: {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

## 5.3) Count developing countries keywords
start_time = time.time()

dev_countries_colnames=['Policy', 'Target', 'Keyword', 'Count', 'Textlength']
#make final count
final_ls = []
##make the count
for item in PDFtext:
    final_doc_ls=[]
    with pd.ExcelWriter(count_file_dict[item[0]], mode='a', engine='openpyxl') as destfile:
        for i in range(0, len(dev_count_keys['Keys'])):
            for j in range(0,len(dev_count_keys['Keys'][i])):
                if len(dev_count_keys['Keys'][i][j]) > 0:
                    counter = 0
                    sentence = item[1]
                    word = str(dev_count_keys['Keys'][i][j])
                    for match in re.finditer(word, sentence):
                        for element in country_ls:
                            #check for element 30 chars before match and until the end of the sentence
                            if element in sentence[match.start()-30:match.start()] or element in sentence[match.end():sentence.find('.',match.end())]:
                                word = word + ' ' + element
                                counter = counter + 1
                    #write counter together with target, policy, keyword as new row in df
                    #first write output to list
                    if counter > 0:
                        row = [item[0], dev_count_keys['Target'][i], word, counter, len(item[1])]
                        final_ls.append(row)
                        final_doc_ls.append(row)
        dfObj = pd.DataFrame(final_doc_ls,columns=dev_countries_colnames)
        dfObj.to_excel(destfile, sheet_name='Dev_countries_raw_count')

final_df = pd.DataFrame(final_ls, columns=dev_countries_colnames)

#drop rows where keyword = ''
# print(len(final_df['Target']))
final_df = final_df[final_df.Keyword != '']
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
final_df = final_df[final_df.Count != 0]
# print(len(final_df['Target']))

#export final output
final_df.to_excel(writer, sheet_name='Dev_countries_raw_count')

with open(log_file, 'a') as f:
    f.write( 
        '- 5.2) Counting developing countries keywords in texts: {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

#policies for which no keys were detected
detected_pol = final_df['Policy'].tolist()

writer.save()

with open(log_file, 'a') as f:
    f.write( 
        '5) Counting keywords in texts: {:.3e} seconds\n\n'.format(time.time()-start_count_time) + 
        'Number of documents: {}\n'.format(len(PDFtext)) +
        'Number of folders: {}'.format(counter)
    )

print('Step 5: Counted keywords in texts.')