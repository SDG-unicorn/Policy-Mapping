import argparse, json, logging, pathlib, pickle, re, time
from itertools import count
import functools as fntl
import datetime as dt

from six import print_
try:
    # For Python =+3.7.
    import importlib.resources as rsrc
except ImportError:
    # Try backported to Python <=3.6 `importlib_resources`.
    import importlib_resources as rsrc
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
#from nltk.tokenize import word_tokenize
from whoosh.lang.porter import stem

##MM imports
import polmap as plmp
import postprocess as pspr
import keywords as kwrd


######################################
########### 0) Define helpstring and arguments to be passed when calling the program
parser = argparse.ArgumentParser(description="""Keyword counting program.
Given a set of keywords, and a set of pdf, docx and html documents in a directory, it counts in each documents how many times a certain keyword is found.
The results are provided for both the whole run and for each documents, together with the raw and stemmed text of the documents and keywords.""")
parser.add_argument('-i', '--input', help='Input directory', default='input')
parser.add_argument('-o', '--output', help='Output directory', default='output')
parser.add_argument('-k', '--keywords', help='Path to keywords file', default=False)
parser.add_argument('-lo', '--label_output', help='Label output dir and files with either a custom string or timestamp if "CurrentTime" is passed as argument', type=str, default=None)

args = parser.parse_args()

########### 1) Define global variables like time, input_dir, ouput_dirs
print("\nBegin text mapping.\n")
start_time = time.time()

input_dir = pathlib.Path(args.input) #if args.input is not None else pathlib.Path('input')
print(f"Input folder is: \n{input_dir}\n")

step = 1

## 1.a) Create output folder structure based on input name, date and time of exectution
if args.label_output == "CurrentTime":
    label_output = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')
elif args.label_output:
    label_output = args.label_output
else:
    label_output = ''

if label_output: print(f"Output label is: \n{label_output}\n")

if args.output == 'output':
    output_directory = pathlib.Path(args.output) / f'{input_dir.name}_{label_output}' #if args.output is not None else pathlib.Path('output') / f'{input_dir.name}_{timestamp}'
else:
    output_directory = pathlib.Path(args.output)

outdirtree_dict = plmp.make_dirtree(output_directory) #Set exist_ok=False later on

for directory in outdirtree_dict.values():
    try:
        directory.mkdir(mode=0o777, parents=True, exist_ok=True)
    except Exception as exception:
        print(f'Creating {directory} raised exception:\n\n{exception}\n\n')
        

if all(directory.is_dir() for directory in outdirtree_dict.values()):
    print('Output directories succesfully created.\n')

if args.label_output:
    project_title=f'{input_dir.name}_{label_output}'
else:
    project_title=''

out_dir, log_dir, processed_keywords_dir, doctext_dir, refs_dir, doctext_stemmed_dir, keyword_count_dir, results_dir, jsonfiles_dir = outdirtree_dict.values()

print(f"Output folder is: \n{out_dir}\n")

## 1.b) Read all files in input directory and select allowed filetypes

allowed_filetypes =  ['.pdf','.html','.mhtml','.doc','.docx','.txt','.rtf'] # ['.doc','.docx'] # 

if input_dir.is_dir(): 
    files = sorted(input_dir.glob('**/*.*'))
    files = [ file for file in files if file.suffix in allowed_filetypes]
elif input_dir.is_file():
    files = [input_dir]

if not (files or input_dir.exists()):
    raise ValueError((f'{input_dir} yields an empty file list. Check if input exists or is not empty'))

policy_documents = pd.DataFrame(files, columns=['Input_files'])
policy_documents.index = policy_documents.index + 1
policy_documents['Paths']=policy_documents['Input_files'].apply(lambda doc_path: pathlib.PurePath(*doc_path.parts[doc_path.parts.index(input_dir.name)+1:]))

policy_documents['Paths'].to_csv(results_dir.joinpath('file_list.txt'), sep='\t', encoding='utf-8')

## 1.c) Create logfile for current run.

log_file = log_dir / f'mapping_{project_title}.log'

if log_file.exists:
    log_file = log_dir / f'mapping_{project_title}.log'
    with open(log_file, 'a') as f:
        f.write( 
            f"\n\nLogfiles already exist, updates appended the \
            {dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')}\n\n"
        )
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

if args.keywords:
    keywords_path = args.keywords
else:    
    with rsrc.path("keywords", "term_matrix.xlsx") as res_path:
        keywords_path = res_path
    
keywords = pd.read_excel(keywords_path, index_col=0)

stop_words = set(stopwords.words('english'))-set(['no','not','nor'])
stop_words.remove('all')

keywd_cols = sorted(set(keywords.columns.to_list()) - set(['Goal', 'Target']))

def stem_text(my_keyword):
    my_keyword = plmp.preprocess_text(str(my_keyword), stop_words)
    return my_keyword

keywords[keywd_cols] = keywords[keywd_cols].applymap(stem_text, na_action='ignore')
labels = keywords[['Goal', 'Target']]

# countries = keywords['developing_countries']['Name'].values.tolist()
# country_ls = []
# for element in countries:
#     element = [re.sub(r'[^a-zA-Z-]+', '', t.lower().strip()) for t in element.split()]
#     # countries = [x.strip(' ') for x in countries]
#     element = [stem(word) for word in element if not word in stop_words]
#     element = ' '.join(element)
#     country_ls.append(element)

keywords_destfilename = processed_keywords_dir / f'{project_title}_processed_{pathlib.Path(keywords_path).name}'

with pd.ExcelWriter(keywords_destfilename, engine='xlsxwriter') as _destfile:
       keywords.to_excel(_destfile, sheet_name="Processed_keywords")

with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Reading and preprocessing keywords in {keywords_path} file: {time.time()-start_time:.3e} seconds\n\n'
    )

print(f'Step {step}: Read and processed keywords in {keywords_path} file.\n')
step += 1

######################################
########### 3) Read document files and convert them into text
start_time = time.time()

doc_texts = {} #This can easily become a dictionary with filepath as a key and text as a value
for counter, file_path in enumerate(files):
    try:
        doc_text = plmp.doc2text(file_path)
       # while '\n\n\n\n' in doc_text : doc_text = doc_text.replace('\n\n\n\n', '\n\n\n') #docx2python specific fix. would probably fit better elsewhere
        textfile_dest_ = file_path.parts[file_path.parts.index(input_dir.name)+1:]
        textfile_dest =  doctext_dir.joinpath(*textfile_dest_)
        textfile_dest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        textfile_dest = textfile_dest.parent / str(textfile_dest.name.replace('.','_')+'.txt')
        with open(textfile_dest, 'w', encoding='utf-8') as file_:
           file_.write(doc_text)
        doc_texts['/'.join(textfile_dest_)] = doc_text
    except Exception as exception: #MM I'd log errors as described in https://realpython.com/python-logging/, we need to test this.
        print(f'{file_path.name}:\n{exception}\n')
        logging.exception(f'{file_path.name} raised exception: {exception} \n\n')


with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Reading, converting and saving {len(doc_texts)} documents as text: {time.time()-start_time:.3e} seconds\n\n'
    )

print(f'Step {step}: Converted {len(doc_texts)} documents to text.\n')
step += 1

#pprint.pprint(doc_texts)
# for policy, text, in doc_texts.items():
#     print(f'{policy} lenght is {len(text)}')

######################################
########### 4) Check for and extract references to SDG agenda in text
start_time = time.time()

with open(results_dir / f'references_to_Agenda2030_{project_title}.json','a') as refs_file:

    references_dict = {}

    for policy, text in doc_texts.items():
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
        references to UN 2030 agenda in {len(doc_texts)} documents: {time.time()-start_time:.3e} seconds\n\n'''
    )

print(f'Step {step}: Found {len(references_dict)} sentences with direct references to UN 2030 Agenda in {len(references_dict)} documents.\n')
step += 1

######################################
########### 5) Preprocess and stem documents texts for counting
start_time = time.time()

for policy, text in doc_texts.items():
    stemmed_text = text.replace('. ', ' . ')
    stemmed_text = re.sub(r'-\n', ' ', stemmed_text)
    stemmed_text = re.sub(r'-{4}([\w.\/]+)-{4}', r' --\1-- ', stemmed_text)
    #stemmed_text = re.sub(r'\n{1,}', ' ', stemmed_text)
    stemmed_text = plmp.preprocess_text(stemmed_text, stop_words)
    item_path = doctext_stemmed_dir / 'stemmed' /pathlib.PurePath(policy) #stemmed_doctext_dir / pathlib.PurePath(item[0])
    item_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    item_path = item_path.parent / (item_path.name.replace('.','_')+'_stemmed.txt')
    with open(item_path, 'w', encoding='utf-8') as stemdoctext:
           stemdoctext.write(f'{stemmed_text}\n\ntextlength: {len(stemmed_text)}')
    #Append textlength
    doc_texts[policy] = { 'text' : text, 'stemmed_text': stemmed_text, 'textlength' : len(stemmed_text)} #MM @


with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Processing and stemming text of {len(doc_texts)} documents: {time.time()-start_time:.3e} seconds\n\n{step+1}) Counting of keywords in text:\n\n'
    )

print(f'Step {step}: Processed and stemmed text from {len(doc_texts)} documents.\n')
step += 1

######################################
########### 6) Counting keywords within text
start_count_time = time.time()
start_time = time.time()

fullcountout = False

target_col_names=['Policy', 'Target', 'Keyword', 'Count', 'Textlength']
count_destfile_dict={}

##make the count
for policy, doc_text in doc_texts.items():

    targetcount_filedest = keyword_count_dir / pathlib.PurePath(policy)
    targetcount_filedest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    targetcount_filedest = targetcount_filedest.parent / (targetcount_filedest.name.replace('.','_')+'.xlsx')
    count_destfile_dict[policy] = targetcount_filedest    

    count_matrix = pd.DataFrame()
    detected_keywords = pd.DataFrame()
    summary = pd.DataFrame()

    count_matrix = keywords[keywd_cols].applymap(lambda keyword: doc_text['stemmed_text'].count(keyword), na_action='ignore')
    count_matrix.fillna(0, inplace=True)

    detected_keywords = keywords[keywd_cols][count_matrix > 0]
    #detected_keywords.fillna(False, inplace=True)

    count_matrix.replace({0: None}, inplace=True)    
      
    count_matrix=pd.merge(labels, count_matrix, left_index=True, right_index=True)
    detected_keywords=pd.merge(labels, detected_keywords, left_index=True, right_index=True)
    
    doc_text['count_matrix'] = count_matrix
    doc_text['detectedkeywd_matrix'] = detected_keywords
    doc_text['marked_text'] = plmp.mark_text(doc_text['stemmed_text'], detected_keywords)

    # with pd.ExcelWriter(targetcount_filedest, mode='w', engine='xlsxwriter') as destfile:
    #     count_matrix.to_excel(destfile, sheet_name='Counts')
    #     detected_keywords.to_excel(destfile, sheet_name='Keywords')    

    # #print(doc_text['marked_text'])
    # item_path = doctext_stemmed_dir / 'marked' / pathlib.PurePath(policy) #stemmed_doctext_dir / pathlib.PurePath(item[0])
    # item_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    # item_path = item_path.parent / (item_path.name.replace('.','_')+'_marked.txt')
    # with open(item_path, 'w', encoding='utf-8') as markdoctext:
    #        markdoctext.write(str(doc_text["marked_text"]))

#Get and write summary data (sum, count and list of keys) for each policy
#For some strange reasons this does not works if done in the previous loop
for policy, item in doc_texts.items():

    # if item['count_matrix'][keywd_cols].dropna().empty:
    #     continue

    # else:
    summary=labels.copy(deep=True)
    count_df = item['count_matrix'].copy(deep=True)
    dtcdterms_df = item['detectedkeywd_matrix'].copy(deep=True)

    termcount_df = pspr.maketermcounttable(count_df, dtcdterms_df)

    summary['Sum_of_keys'] = count_df[keywd_cols].sum(axis=1)
    summary['Count_of_keys'] = dtcdterms_df[keywd_cols].count(axis=1) #Use explicit fraction?
    summary['list_of_keys'] = dtcdterms_df[keywd_cols].apply(plmp.join_str, raw=True, axis=1)
    summary = summary[summary['Count_of_keys'] > 0]

    with pd.ExcelWriter(count_destfile_dict[policy], mode='w', engine='xlsxwriter') as destfile:
        summary.to_excel(destfile, sheet_name='Summary')
        termcount_df.to_excel(destfile, sheet_name='Terms_count')


count_matrixes = [ doc_text['count_matrix'] for doc_text in doc_texts.values() ]
total_count = fntl.reduce(lambda a, b: a[keywd_cols].add(b[keywd_cols], fill_value=0), count_matrixes)
total_keywords =  keywords[keywd_cols][total_count[keywd_cols] > 0]

# Using reduce with df.count will give the number of policies adressing a certain target
# This can be leveraged to build sankey diagrams and poilicy mapping for the platform

total_count = pd.merge(labels, total_count[keywd_cols], left_index=True, right_index=True)
total_keywords = pd.merge(labels, total_keywords, left_index=True, right_index=True)

total_termcount_df = pspr.maketermcounttable(total_count, total_keywords)

total_summary=labels.copy(deep=True)
total_summary['Sum_of_keys'] = total_count[keywd_cols].sum(axis=1)
total_summary['Count_of_keys'] = total_keywords[keywd_cols].count(axis=1) #Use explicit fraction?
total_summary['list_of_keys'] = total_keywords[keywd_cols].apply(plmp.join_str, raw=True, axis=1)
total_summary = total_summary[total_summary['Count_of_keys'] > 0]

count_destfile = results_dir / f'mapping_{project_title}.xlsx'

try:
    with pd.ExcelWriter(count_destfile, mode='w', engine='xlsxwriter') as destfile:
        total_summary.to_excel(destfile, sheet_name='Summary')
        total_termcount_df.to_excel(destfile, sheet_name='Terms_count')

except Exception as exception:
    print(f'Writing totaL raised: \n{exception}\n')
    logging.exception(f'Writing total raised: {exception} \n\n')
    
print(f'Final results are stored in:\n{count_destfile}\n')

with open(log_file, 'a') as f:
    f.write( 
        f'- Total keywords counting time: {time.time()-start_count_time:.3e} seconds.\n\n'
        )

print(f'Step {step}: Counted keywords in texts.\n')
step += 1

######################################
########### 7) Process results for visualization

start_time = time.time() 

with rsrc.path("keywords", "goal_target_list.xlsx") as pp_path:
    pp_def = pd.read_excel(pp_path)

priorities_df=pspr.make_polpridf(total_summary, pp_def)

# 7.1) create and export json files for bubblecharts on knowSDGs platform ## Fix this

sdg_bubbleplot_dict=pspr.make_sdgbubbleplot(total_summary)
sdg_bubbles = jsonfiles_dir / 'sdg_bubbles.json'
with sdg_bubbles.open(mode='w', encoding='utf-8') as f:
    json.dump(sdg_bubbleplot_dict, f)


priority_bubbleplot_dict=pspr.make_polpribubbleplot(priorities_df)
priority_bubbles = jsonfiles_dir / 'priority_bubbles.json'
with priority_bubbles.open(mode='w', encoding='utf-8') as f:
    json.dump(priority_bubbleplot_dict, f)

bubblecharts_exists = all([pathlib.Path(sdg_bubbles).exists(), pathlib.Path(priority_bubbles).exists()])

with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Jsonfiles for sdg and priorities bubblecharts succesfully created: {bubblecharts_exists}\n{time.time()-start_count_time:.3e} seconds.\n\n'
        )

print(f'\nStep {step}: Jsonfiles for sdg and priorities bubblecharts succesfully created: {bubblecharts_exists}\n')
step += 1

with open(log_file, 'a') as f:
    f.write( 
        f'Mapping completed'
        )

print('Mapping completed')