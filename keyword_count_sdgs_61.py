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
import polmap.polmap as plmp
import postprocess.postprocess as pspr
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
    with rsrc.path("keywords", "keywords_expanded_manually_reordered.xlsx") as res_path:
        keywords_path = res_path
    
keywords = pd.read_excel(res_path, index_col=0)

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
    #stemmed_text = re.sub(r'\n{1,}', ' ', stemmed_text)
    stemmed_text = plmp.preprocess_text(stemmed_text, stop_words)
    item_path = doctext_stemmed_dir / pathlib.PurePath(policy) #stemmed_doctext_dir / pathlib.PurePath(item[0])
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
    detected_keywords.fillna('', inplace=True)

    count_matrix.replace({0: None}, inplace=True)    
      
    count_matrix=pd.merge(labels, count_matrix, left_index=True, right_index=True)
    detected_keywords=pd.merge(labels, detected_keywords, left_index=True, right_index=True)

    summary=pd.DataFrame(labels)

    # summary['Sum_of_keys'] = count_matrix[keywd_cols].sum(axis=1)
    # summary['Count_of_keys'] = detected_keywords[keywd_cols].count(axis=1)
    # summary['list_of_keys'] = detected_keywords[keywd_cols].apply(plmp.join_str, raw=True, axis=1)
    
    with pd.ExcelWriter(targetcount_filedest, mode='w', engine='xlsxwriter') as destfile:
        count_matrix.to_excel(destfile, sheet_name='Counts')
        detected_keywords.to_excel(destfile, sheet_name='Keywords')
        summary.to_excel(destfile, sheet_name='Summary')

        # summary['Sum_of_keys'] = count_matrix[keywd_cols].sum(axis=1)
        # summary['Count_of_keys'] = detected_keywords[keywd_cols].count(axis=1)
        # summary['list_of_keys'] = detected_keywords[keywd_cols].apply(plmp.join_str, raw=True, axis=1)
        # summary.to_excel(destfile, sheet_name='Summary')

    doc_text['count_matrix'] = count_matrix
    doc_text['detectedkeywd_matrix'] = detected_keywords
    doc_text['marked_text'] = plmp.mark_text(doc_text['stemmed_text'], detected_keywords)

    #print(doc_text['marked_text'])
    item_path = doctext_stemmed_dir / pathlib.PurePath(policy) #stemmed_doctext_dir / pathlib.PurePath(item[0])
    item_path = item_path.parent / (item_path.name.replace('.','_')+'_marked.txt')
    with open(item_path, 'w', encoding='utf-8') as markdoctext:
           markdoctext.write(str(doc_text["marked_text"]))

count_matrixes = [ doc_text['count_matrix'] for doc_text in doc_texts.values()]

# df1 = pd.DataFrame({'val':{'a': 1, 'b':2, 'c':3}})
# df2 = pd.DataFrame({'val':{'a': 1, 'b':2, 'd':3}})
# df3 = pd.DataFrame({'val':{'e': 1, 'c':2, 'd':3}})
# df4 = pd.DataFrame({'val':{'f': 1, 'a':2, 'd':3}})
# df5 = pd.DataFrame({'val':{'g': 1, 'f':2, 'd':3}})

total_count = fntl.reduce(lambda a, b: a[keywd_cols].add(b[keywd_cols], fill_value=0), count_matrixes)

total_count = pd.merge(labels, total_count, left_index=True, right_index=True)

# total_count = pd.DataFrame()
# for policy, item in doc_texts.items():
#     total_count = total_count.add(item['count_matrix'], fill_value=0)

count_destfile = results_dir / f'mapping_{project_title}.xlsx'

# with pd.ExcelWriter(count_destfile, engine='openpyxl') as _destfile:
#     target_df = pd.DataFrame(target_ls, columns=target_col_names)
#     target_df.to_excel(_destfile, sheet_name = 'Target_raw_count' )

with pd.ExcelWriter(count_destfile, mode='w', engine='xlsxwriter') as writer:

    try:
        total_count.to_excel(writer, sheet_name='Keyword_count')
    except Exception as exception:
            print(f'Writing target counts raised: \n{exception}\n')
            logging.exception(f'Writing target counts raised: {exception} \n\n')
    #writer.save()
print(f'Final results are stored in:\n{count_destfile}\n')

with open(log_file, 'a') as f:
    f.write( 
        f'- {step+0.1}) Counting target keywords in texts: {time.time()-start_time:.3e} seconds\n\n'
    )

with open(log_file, 'a') as f:
    f.write( 
        f'- Total keywords counting time: {time.time()-start_count_time:.3e} seconds.\n\n'
        )

print(f'Step {step}: Counted keywords in texts.\n')
step += 1

# target_df.to_pickle("gd_target_df.pkl")
# goal_df.to_pickle("gd_goal_df.pkl")

target_df['Group']=target_df['Policy'].apply(lambda x_str: x_str.split('/')[0])

######################################
########### 7) Postprocessing of keyword count

start_time = time.time()

target_df['Target'] = pspr.stringify_id(target_df['Target'])

results_dict = {}

#sdg_df=pspr.sdg_reference_df #MM we need to have that file available whenever running the script from other locations.
with rsrc.path("keywords", "goal_target_list.xlsx") as res_path:
    sdg_df = pd.read_excel(res_path)

## 7.1) Aggregate count of keywords to target-level --> export this to final results workbook
results_dict['target_dat'] = pspr.aggregate_to_targets(target_df, sdg_df)

results_dict['target_dat_pp'] = results_dict['target_dat'].copy()
if not results_dict['target_dat'].empty:
    results_dict['target_dat'] = results_dict['target_dat'].drop(columns=['MAIN_priority', 'SEC_priority'])
else:
    pass

# ## 7.2) Filter out target counts based on number of counts, number of keywords and textlenght --> export this to final results workbook
# #results_dict['dat_filtered'] = pspr.filter_data(results_dict['target_dat'])

# ## 7.3) get overview on target-level --> export this to final results workbook
results_dict['target_overview_df'] = pspr.get_target_overview(results_dict['target_dat'], sdg_df)

# ## 7.4) get undetected targets --> export this to final results workbook
# #results_dict['undetected_targets'] = pspr.find_undetected_targets(results_dict['target_dat'], sdg_df)

## 7.5)  aggregate goal counts to goal-level --> export this to final results workbook
results_dict['goal_dat'] = pspr.aggregate_to_goals(goal_df, sdg_df) #MM What if no goals are detected? We need to handle this scenario

# # 7.6) get goal_overview from target counts and goal counts --> export this to final results workbook
results_dict['goal_overview'] = pspr.get_goal_overview(results_dict['target_dat'], results_dict['goal_dat'], sdg_df)

# # 7.7) group by document and aggregate to goals, when running this sheetname list  and sheetnames need to be adapted
# results_dict['goals_grouped_by_document'] = pspr.group_by_name_and_get_goaloverview(results_dict['target_dat'], results_dict['goal_dat'], sdg_df)

# # 7.8) get goal overview but not with aggregated counts but with number of policies relating to a goal
# results_dict['policies_per_goal'] = pspr.get_number_of_policies_per_goal(results_dict['target_dat'], results_dict['goal_dat'])

# # 7.9) get list of priorities
results_dict['priorities'] = pspr.map_target_dat_to_priorities(results_dict['target_dat_pp'], sdg_df)

# results_dict['target_dat_by_group'] = pspr.aggregate_to_targets(target_df, sdg_df, grouping_factor='Group')
# results_dict['goal_dat_by_group'] = pspr.aggregate_to_goals(goal_df, sdg_df, grouping_factor='Group')
# results_dict['goals_grouped_by_folder'] = pspr.group_by_name_and_get_goaloverview(results_dict['target_dat_by_group'], results_dict['goal_dat_by_group'], sdg_df, grouping_factor='Group')

# with open('results.pkl', 'wb') as pkl_f:
#     pickle.dump(results_dict, pkl_f)

sheetnames_list = ['target_count', 'filtered_target_count', 'undetected_targets', 'goal_count', 'goal_overview', 'total_count_(goals_+_targets)', 'priorities']


# sheetnames_list = ['target_count', 'filtered_target_count', 'undetected_targets', 'goal_count', 'goal_overview', 'total_count_by_document', 'total_count']

# sheetnames = { df : sheetname for df, sheetname in zip(list(results_dict.keys()), sheetnames_list)}

# pprint.pprint(sheetnames)

mappingresults_destfile = results_dir / f'results_{project_title}.xlsx'

#Skip saving if all df are ampty or save an empyt excel file?
with pd.ExcelWriter(mappingresults_destfile, mode='w', engine='xlsxwriter') as destfile:
    for sheetname, df in results_dict.items():#zip( sheetnames.values()):

        #print(f'\n{} - {}')
        if not df.empty:
            df.to_excel(destfile, sheet_name=sheetname)


with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Analyzed results and saved summary tables in {mappingresults_destfile}\n{time.time()-start_count_time:.3e} seconds.\n\n'
        )

print(f'Step {step}: Analyzed results and saved summary tables in {mappingresults_destfile}\n')
step += 1

######################################
########### 8) Create JSON files for visualization

# 8.1) create and export json files for bubblecharts on knowSDGs platform ## Fix this

start_time = time.time() 

sdg_bubbleplot_dict=pspr.create_json_files_for_bubbleplots(results_dict['target_overview_df'].fillna(""), results_dict['goal_overview'])
sdg_bubbles = jsonfiles_dir / 'sdg_bubbles.json'
with sdg_bubbles.open(mode='w', encoding='utf-8') as f:
    json.dump(sdg_bubbleplot_dict, f)


# 8.2) create and export json files for bubblecharts on political priorities
priority_bubbleplot_dict=pspr.create_json_for_priorities(results_dict['priorities'])
priority_bubbles = jsonfiles_dir / 'priority_bubbles.json'
with priority_bubbles.open(mode='w', encoding='utf-8') as f:
    json.dump(priority_bubbleplot_dict, f)

bubblecharts_exists = all([pathlib.Path(sdg_bubbles).exists, pathlib.Path(priority_bubbles).exists])

with open(log_file, 'a') as f:
    f.write( 
        f'{step}) Jsonfiles for sdg and priorities bubblecharts succesfully created: {bubblecharts_exists}\n{time.time()-start_count_time:.3e} seconds.\n\n'
        )

print(f'\nStep {step}: Jsonfiles for sdg and priorities bubblecharts succesfully created: {bubblecharts_exists}\n')
step += 1

#To be moved somewhere in modules
# pp_colors={'Human Development':'#F68D4A',
# 'Growth Jobs':'#FABE13',
# 'Green Deal':'#1A6835',
# 'Governance':'#005C95',
# 'Digitalisation':'#4D9CD5',
# 'Migration':'#DE6189',
# 'None':'#000000'
# }

# results_dict['priorities'].rename(columns = {'priority':'name', 'Count':'size'}, inplace = True)
# results_dict['priorities']['goal_color']=results_dict['priorities']['name'].map(pp_colors)
# pp_bubbleplot_dict= {'name': 'pp',
# 'children': list(results_dict['priorities'].to_dict('index').values())}
# polprior_bubbles = jsonfiles_dir / 'polprior_bubbles.json'
# with polprior_bubbles.open(mode='w', encoding='utf-8') as f:
#     json.dump(pp_bubbleplot_dict, f)
#
# print(jsonfiles_dir)

#MM 11,12,13 for the moment not needed

# 11.) export individual json files for each policy, input for individual sankey charts on knowSDGs platform
# sankeychart_dict=pspr.create_json_files_for_sankey_charts(results_dict['info_added_df'])
# sankeychart_path = jsonfiles_dir / 'sankeychart.json'
# with sankeychart_path.open(mode='w', encoding='utf-8') as f:
#     json.dump(sankeychart_dict, f)

# # 12.) export csv table with list of policies (second viz on knowSDGs platform = List of Policies)
# #policy_df = export_csv_for_policy_list(info_added_df)

# # 13.) create and export policy coherence df (third viz knowSDGs platform)
# # pol_coher_df=create_policy_coherence_data(dat_filtered, sdg_df)#output_path=out_dir
# # pol_coher_df.to_csv((pathlib.Path(out_dir) / 'policy_coherence.csv'), sep=";", index=False, encoding='utf-8-sig')

with open(log_file, 'a') as f:
    f.write( 
        f'Mapping completed'
        )

print('Mapping completed')