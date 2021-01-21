import io, csv, re, os, json
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
from whoosh.lang.porter import stem
from nltk.stem import WordNetLemmatizer
from io import StringIO
import xlsxwriter
from itertools import chain
##MM imports
import datetime as dt
import pathlib
import logging
import time

from docx2python import docx2python

from polmap.polmap import preprocess_text, doc2text # replaced the keyword processing block


######################################
########### 1) Define global variables like time, input_dir, ouput_dirs
print('Begin text mapping.\n')
start_time = time.time()

## 1.a) Read all files in input directory and select allowed filetypes

input_dir = pathlib.Path.cwd() / 'pdf_re' / 'Test' #MM let user provide an input dir
input_folder_name = input_dir.name

allowed_filetypes=['.pdf','.html','.mhtml','.doc','.docx']

files = sorted(input_dir.glob('**/*.*'))
files = [ file for file in files if file.suffix in allowed_filetypes]
#MM assert files==False and log assertion error.

## 1.b) Create output folder structure based on input name, date and time of exectution

date = dt.datetime.now().date().isoformat() #def make_directories(project='TEI'): #MM start func definition
hour = dt.datetime.now().time().isoformat(timespec='seconds').replace(':', '')
current_date = '_'+date+'_T'+hour

project_title = input_folder_name+str(current_date) 

out_dir = pathlib.Path.cwd() / 'output' / project_title #Beginning of try block
log_dir = out_dir / 'logs'
results_dir = out_dir / 'results'
docs2txt_dir = out_dir / 'docs2txt'
stemmed_doctext_dir = out_dir / 'docs2txt_stemmed'

dir_dict = { directory: directory.mkdir(mode=0o777, parents=True, exist_ok=True) for directory in [out_dir, log_dir, results_dir, docs2txt_dir, ] } #Set exist_ok=False later on
#except FileExistsError, Error : #MM Deal with cases where directory creation failed. Error occurring here will not be catched in the log.
print('Output folder is: \n'+str(out_dir)+'\n')
#return #MM end func 

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

keys = pd.read_excel('keys_update_15012020.xlsx', sheet_name= 'Target_keys' ) #MM 'keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'Sheet1' 
goal_keys = pd.read_excel('keys_update_15012020.xlsx', sheet_name= 'Goal_keys' ) #MM Create a dictionary of dataframes for each sheet
dev_count_keys = pd.read_excel('keys_update_15012020.xlsx', sheet_name= 'MOI' ) #MM 'keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'Sheet2' 

#remove all from stop_words to keep in keywords
stop_words = set(stopwords.words("english"))
stop_words.remove("all")

keys['Keys']=keys['Keys'].apply(lambda x: preprocess_text(x, stop_words))
goal_keys['Keys']=goal_keys['Keys'].apply(lambda x: preprocess_text(x, stop_words))
dev_count_keys['Keys']=dev_count_keys['Keys'].apply(lambda x: preprocess_text(x, stop_words))

##Country names
countries_in = pd.read_excel('keys_update_15012020.xlsx', sheet_name= 'developing_countries') #MM 'keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'developing_countries'
countries = countries_in['Name'].values.tolist()
country_ls = []
for element in countries:
    element = [re.sub(r"[^a-zA-Z-]+", '', t.lower().strip()) for t in element.split()]
    # countries = [x.strip(' ') for x in countries]
    element = [stem(word) for word in element if not word in stop_words]
    element = ' '.join(element)
    country_ls.append(element)

with open(log_file, 'a') as f:
    f.write( 
        '2) Reading and preprocessing keywords: {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

print('Step 2: Read and processed keywords.\n')
######################################
########### 3) Read document files and convert them into text
start_time = time.time()

PDFtext = []
counter = 0
for doc_path in files:
    counter += 1
    try:
        policy_text=[]
        doc_text = doc2text(doc_path)
        while '\n\n\n\n' in doc_text : doc_text = doc_text.replace('\n\n\n\n', '\n\n\n') #docx2python specific fix. would probably fit better elsewhere
        policy_text.append(doc_text)
        doctext_ = doc_path.parts[doc_path.parts.index(input_dir.name)+1:]
        doctext_name =  docs2txt_dir.joinpath(*doctext_)
        doctext_name.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        doctext_name = doctext_name.parent.joinpath(doctext_name.stem+'.txt')
        with open(doctext_name, 'w') as file_:
           file_.write(doc_text)
        PDFtext.append(['/'.join(doctext_),' ; '.join(policy_text)])
    except Exception as excptn: #MM I'd log errors as described in https://realpython.com/python-logging/, we need to test this.
        logging.exception('{doc_file} raised exception {exception} \n\n'.format(doc_file=doc_item.name, exception=excptn))


with open(log_file, 'a') as f:
    f.write( 
        '3) Reading, converting and saving {docs} documents as text: {seconds:.3e} seconds\n\n'.format(docs=len(PDFtext),seconds=(time.time()-start_time))
    )

print('Step 3: Converted {docs} documents to text.\n'.format(docs=len(PDFtext)))
######################################
########### 4) Read document files and convert them into text
start_time = time.time()

lemmatizer = WordNetLemmatizer()
for item in PDFtext:
    #detect soft hyphen that separates words
    item[1] = item[1].replace('.', ' .')
    item[1] = [re.sub(r'-\n', '', t) for t in item[1].split()]
    #get indices of soft hyphens
    indices = [i for i, s in enumerate(item[1]) if '\xad' in s]
    #merge the separated words
    for index in indices:
        item[1][index] = item[1][index].replace('\xad', '')
        item[1][index+1] = item[1][index]+item[1][index+1]
    #remove unnecessary list elements
    for index in sorted(indices, reverse=True):
        del item[1][index]
    #remove special character, numbers, lowercase #MM from here until @ this code is identical to prepare keywords correct?
    item[1] = [re.sub(r"[^a-zA-Z-\.]+", '', t.lower().strip()) for t in item[1]]
    #add whitespaces
    item[1] = [word.center(len(word)+2) for word in item[1]]
    #recover R&D for detection
    item[1] = [w.replace(" rd ", "R&D") for w in item[1]]
    # remove words > 2
    item[1] = [word for word in item[1] if len(word) > 2 or word == "ph"]
    # remove '
    # item[1] = [s.replace('\'', '') for s in item[1]]
    #remove whitespaces
    item[1] = [x.strip(' ') for x in item[1]]
    #add special char to prevent aids from being stemmed to aid
    item[1] = [w.replace("aids", "ai&ds&") for w in item[1]]
    item[1] = [w.replace("productivity", "pro&ductivity&") for w in item[1]]
    item[1] = [w.replace("remittances", "remit&tance&") for w in item[1]]
    item[1] = [w.replace("remittance", "remit&tance&") for w in item[1]]
    # stem words
    item[1] = [stem(word) for word in item[1] if not word in stop_words]
    #remove special char for detection in text
    item[1] = [w.replace("ai&ds&", "aids") for w in item[1]]
    item[1] = [w.replace("pro&ductivity&", "productivity") for w in item[1]]
    item[1] = [w.replace("remit&tance&", "remittance") for w in item[1]]
    #try lemmatizing
    # item[1] = [lemmatizer.lemmatize(word) for word in item[1] if not word in stop_words]
    # merge back together to 1 string
    item[1] = ' '.join(item[1])
    #add trailing leading whitespace
    item[1] = " " + item[1] + " "
    #save out
    item_path = stemmed_doctext_dir / pathlib.PurePath(item[0]) #stemmed_doctext_dir / pathlib.PurePath(item[0])
    item_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    item_path = item_path.parent.joinpath(item_path.stem+'_stemmed.txt')
    with open(item_path, 'w') as stemdoctext:
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
target_ls = []
##make the count
for item in PDFtext:
    for i in range(0, len(keys['Keys'])):
        for j in range(0,len(keys['Keys'][i])):
            # print(keys['Keys'][i][j])
            counter = item[1].count(str(keys['Keys'][i][j]))
            #write counter together with target, policy, keyword as new row in df
            #first write output to list
            target_ls.append([item[0], keys['Target'][i], keys['Keys'][i][j], counter, len(item[1])])

target_df = pd.DataFrame(target_ls, columns=['Policy', 'Target', 'Keyword', "Count", "Textlength"])

#drop rows where keyword = ""
# print(len(final_df['Target']))
target_df = target_df[target_df.Keyword != ""]
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
target_df = target_df[target_df.Count != 0]
# print(len(final_df['Target']))

# Create a Pandas Excel writer using XlsxWriter as the engine.

write_name = results_dir / 'mapping_{}.xlsx'.format(project_title)
writer = pd.ExcelWriter(write_name, engine='xlsxwriter')
#SB writer = pd.ExcelWriter(os.getcwd()+str("\\results\\raw\\mapping_TEI_{}.xlsx").format(current_date), engine='xlsxwriter')

#export final output
target_df.to_excel(writer, sheet_name='Target_raw_count')

with open(log_file, 'a') as f:
    f.write( 
        '- 5.1) Counting target keywords in texts: {:.3e} seconds\n\n'.format(time.time()-start_time)
    )

## 5.2) Count Goals keywords
start_time = time.time()

goal_ls = []
##make the count
for item in PDFtext:
    for i in range(0, len(goal_keys['Keys'])):
        for j in range(0,len(goal_keys['Keys'][i])):
            # print(keys['Keys'][i][j])
            counter = item[1].count(str(goal_keys['Keys'][i][j]))
            #write counter together with target, policy, keyword as new row in df
            #first write output to list
            goal_ls.append([item[0], goal_keys['Goal'][i], goal_keys['Keys'][i][j], counter, len(item[1])])

goal_df = pd.DataFrame(goal_ls, columns=['Policy', 'Goal', 'Keyword', "Count", "Textlength"])

#drop rows where keyword = ""
# print(len(final_df['Target']))
goal_df= goal_df[goal_df.Keyword != ""]
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

#make final count
final_ls = []
##make the count
for item in PDFtext:
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
                            word = word + " " + element
                            counter = counter + 1
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                if counter != 0:
                    final_ls.append([item[0], dev_count_keys['Target'][i], word, counter, len(item[1])])

final_df = pd.DataFrame(final_ls, columns=['Policy', 'Target', 'Keyword', "Count", "Textlength"])

#drop rows where keyword = ""
# print(len(final_df['Target']))
final_df = final_df[final_df.Keyword != ""]
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