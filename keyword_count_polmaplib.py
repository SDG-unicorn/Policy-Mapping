import re, json, pathlib, logging, time, argparse
import datetime as dt
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
from whoosh.lang.porter import stem
from itertools import chain

##MM imports
import polmap.polmap as plmp


######################################
########### 0) Define helpstring and arguments to be passed when calling the program
parser = argparse.ArgumentParser(description="""Keyword counting program.
Given a set of keywords, and a set of pdf, docx and html documents in a directory, it counts in each documents how many times a certain keyword is found.
The results are provided for both the whole run and for each documents, together with the raw and stemmed text of the documents and keywords.""")
parser.add_argument('-i', '--input', help='Input directory')
parser.add_argument('-o', '--output', help='Output directory')
parser.add_argument('-k', '--keywords', help='Keywords file')
#parser.add_argument('-at', '--add_timestamp', help='Add a timestamp to output directory')

args = parser.parse_args()

########### 1) Define global variables like time, input_dir, ouput_dirs
print("\nBegin text mapping.\n")
start_time = time.time()

input_dir = pathlib.Path(args.input) if args.input != None else pathlib.Path('input')
print(f"Input folder is: \n{input_dir}\n")

step = 1

## 1.a) Create output folder structure based on input name, date and time of exectution

timestamp = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

output_directory = pathlib.Path(args.output) if args.output != None else pathlib.Path('output') / f'{input_dir.name}_{timestamp}'

outdirtree_dict = plmp.make_dirtree(output_directory) #Set exist_ok=False later on

for directory in outdirtree_dict.values():
    try:
        directory.mkdir(mode=0o777, parents=True, exist_ok=True)
    except Exception as exception:
        print(f'Creating {directory} raised exception:\n\n{exception}\n\n')
        

if all(directory.is_dir() for directory in outdirtree_dict.values()):
    print('Output directories succesfully created.\n')
    
project_title=outdirtree_dict['out_dir'].name

out_dir, log_dir, results_dir, processed_keywords_dir, doctext_dir, refs_dir ,doctext_stemmed_dir, keyword_count_dir = outdirtree_dict.values()

print(f"Output folder is: \n{out_dir}\n")

## 1.b) Read all files in input directory and select allowed filetypes

allowed_filetypes =  ['.pdf','.html','.mhtml','.doc','.docx'] # ['.doc','.docx'] # 

files = sorted(input_dir.glob('**/*.*'))
files = [ file for file in files if file.suffix in allowed_filetypes]

policy_documents = pd.DataFrame(files, columns=['Input_files'])
policy_documents.index = policy_documents.index + 1
policy_documents['Paths']=policy_documents['Input_files'].apply(lambda doc_path: pathlib.PurePath(*doc_path.parts[doc_path.parts.index(input_dir.name)+1:]))

policy_documents['Paths'].to_csv(results_dir.joinpath('file_list.txt'), sep='\t', encoding='utf-8')

## 1.c) Create logfile for current run.

log_file = log_dir / f'mapping_{project_title}.log'
log_file.touch(mode=0o666)
logging.basicConfig(filename=log_file, filemode='a', level=logging.WARNING)

with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Creating folders, reading input folder and listing all file paths : {time.time()-start_time:.3e} seconds\n\n'
    )

print(f'Step {step}: Listed paths of documents and created main output folders.\n')
step += 1


######################################
########### 2) MM Read the list of keywords and apply the prepare_keyords text processing function from polmap
start_time = time.time()

keywords_excel = pathlib.Path(args.keywords) if args.keywords != None else pathlib.Path('keywords/keywords.xlsx')

#keywords_sheets= [Targ]

keys = pd.read_excel(keywords_excel, sheet_name= 'Target_keys' ) 
goal_keys = pd.read_excel(keywords_excel, sheet_name= 'Goal_keys' )
dev_count_keys = pd.read_excel(keywords_excel, sheet_name= 'MOI' )

#remove all from stop_words to keep in keywords
stop_words = set(stopwords.words('english'))
stop_words.remove('all')

keys['Keys']=keys['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))
goal_keys['Keys']=goal_keys['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))
dev_count_keys['Keys']=dev_count_keys['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))

keys['Keys']=keys['Keys'].apply(lambda keywords: [plmp.preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])
goal_keys['Keys']=goal_keys['Keys'].apply(lambda keywords: [plmp.preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])
dev_count_keys['Keys']=dev_count_keys['Keys'].apply(lambda keywords: [plmp.preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])

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

keywords_filename = processed_keywords_dir / f'{project_title}_processed_{keywords_excel.name}'
keywords_filename = pd.ExcelWriter(keywords_filename, engine='openpyxl')
keys.to_excel(keywords_filename, sheet_name='Targets_kwrds')
goal_keys.to_excel(keywords_filename, sheet_name='Goal_kwrds')
dev_count_keys.to_excel(keywords_filename, sheet_name='MOI_kwrds')
pd.DataFrame(country_ls,columns=['Name']).to_excel(keywords_filename, sheet_name='dev_countries_kwrds')
keywords_filename.save()

with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Reading and preprocessing keywords in {keywords_excel} file: {time.time()-start_time:.3e} seconds\n\n'
    )

print(f'Step {step}: Read and processed keywords in {keywords_excel} file.\n')
step += 1

######################################
########### 3) Read document files and convert them into text
start_time = time.time()

PDFtext = [] #This can easily become a dictionary with filepath as a key and text as a value
counter = 0
for file_path in files:
    counter += 1
    try:
        doc_text = plmp.doc2text(file_path)
       # while '\n\n\n\n' in doc_text : doc_text = doc_text.replace('\n\n\n\n', '\n\n\n') #docx2python specific fix. would probably fit better elsewhere
        textfile_dest_ = file_path.parts[file_path.parts.index(input_dir.name)+1:]
        textfile_dest =  doctext_dir.joinpath(*textfile_dest_)
        textfile_dest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        textfile_dest = textfile_dest.parent / str(textfile_dest.name.replace('.','_')+'.txt')
        with open(textfile_dest, 'w', encoding='utf-8') as file_:
           file_.write(doc_text)
        PDFtext.append(['/'.join(textfile_dest_),doc_text])
    except Exception as exception: #MM I'd log errors as described in https://realpython.com/python-logging/, we need to test this.
        print(exception)
        logging.exception(f'{file_path.name} raised exception: {exception} \n\n')


with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Reading, converting and saving {len(PDFtext)} documents as text: {time.time()-start_time:.3e} seconds\n\n'
    )

print(f'Step {step}: Converted {len(PDFtext)} documents to text.\n')
step += 1

######################################
########### 4) Check for and extract references to SDG agenda in text
start_time = time.time()

with open(results_dir / f'{project_title}_Agenda2030_references.json','a') as refs_file:

    references_dict = {}

    for policy, text in PDFtext:
        refs = plmp.SDGrefs_mapper(text)
        if bool(refs):
            references_dict[str(policy)] = {'References' : refs, 'Number of sentences' : len(refs)}

    json.dump(references_dict, refs_file)

    for policies, references in references_dict.items():

        dest = refs_dir / f"{policies.replace('.','_')}.json"
        dest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)

        with open(dest, 'a') as docref_file:
            json.dump(references, docref_file)


with open(log_file, 'a') as f:
    f.write( 
        f'''{step}) Finding and extracting {len(references_dict)} sentences with direct
        references to UN 2030 agenda in {len(PDFtext)} documents: {time.time()-start_time:.3e} seconds\n\n'''
    )

print(f'Step {step}: Found {len(references_dict)} sentences with direct references to UN 2030 Agenda in {len(references_dict)} documents.\n')
step += 1

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
    item[1] = plmp.preprocess_text(item[1], stop_words)
    #item[1] = item[1].replace(' . ', ' . \n')
    #save out
    item_path = doctext_stemmed_dir / pathlib.PurePath(item[0]) #stemmed_doctext_dir / pathlib.PurePath(item[0])
    item_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    item_path = item_path.parent / (item_path.name.replace('.','_')+'_stemmed.txt')

    with open(item_path, 'w', encoding='utf-8') as stemdoctext:
           stemdoctext.write(f'{item[1]}\n\nTextlenght: {len(item[1])}')
    #Append textlenght
    item = item.append(len(item[1])) #MM @


with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Processing and stemming text of {len(PDFtext)} documents: {time.time()-start_time:.3e} seconds\n\n{step+1}) Counting of keywords in text:\n\n'
    )

print(f'Step {step}: Processed and stemmed text from {len(PDFtext)} documents.\n')
step += 1

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
        destfile.save()
    

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

write_name = results_dir / f'mapping_{project_title}.xlsx'
writer = pd.ExcelWriter(write_name, engine='openpyxl')

print(f'Final results are stored in:\n{write_name}\n')

#export final output
target_df.to_excel(writer, sheet_name='Target_raw_count')
#writer.save()

with open(log_file, 'a') as f:
    f.write( 
        f'- {step+0.1}) Counting target keywords in texts: {time.time()-start_time:.3e} seconds\n\n'
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
        destfile.save()
                

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
        f'- {step+0.2}) Counting goal keywords in texts: {time.time()-start_time:.3e} seconds\n\n'
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
        destfile.save()

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
        f'- {step+0.3}) Counting developing countries keywords in texts: {time.time()-start_time:.3e} seconds\n\n'
    )

#policies for which no keys were detected
detected_pol = final_df['Policy'].tolist()

writer.save()


with open(log_file, 'a') as f:
    f.write( 
        f'- Total keywords counting time: {time.time()-start_count_time:.3e} seconds.'
        )

print(f'Step {step}: Counted keywords in texts.')