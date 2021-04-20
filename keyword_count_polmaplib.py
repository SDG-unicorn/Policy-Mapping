import argparse, json, logging, pathlib, pprint, re, time
import datetime as dt
import importlib.resources as rsrc
from nltk.corpus import stopwords
import pandas as pd
#from nltk.tokenize import word_tokenize
from whoosh.lang.porter import stem

##MM imports
import polmap.polmap as plmp
import postprocess.postprocess as pspr


######################################
########### 0) Define helpstring and arguments to be passed when calling the program
parser = argparse.ArgumentParser(description="""Keyword counting program.
Given a set of keywords, and a set of pdf, docx and html documents in a directory, it counts in each documents how many times a certain keyword is found.
The results are provided for both the whole run and for each documents, together with the raw and stemmed text of the documents and keywords.""")
parser.add_argument('-i', '--input', help='Input directory', default='input')
parser.add_argument('-o', '--output', help='Output directory', default='output')
parser.add_argument('-k', '--keywords', help='Path to keywords file', default=False)
#parser.add_argument('-ref', '--sdg_reftable', help='SDG reference table file', default='postprocess/goal_target_list.xlsx')
parser.add_argument('-lo', '--label_output', help='Label parent output directory and outputfiles with {input dir name}_{timestamp}', type=bool, default=False)

args = parser.parse_args()

########### 1) Define global variables like time, input_dir, ouput_dirs
print("\nBegin text mapping.\n")
start_time = time.time()

input_dir = pathlib.Path(args.input) #if args.input is not None else pathlib.Path('input')
print(f"Input folder is: \n{input_dir}\n")

step = 1

## 1.a) Create output folder structure based on input name, date and time of exectution
if args.label_output:
    timestamp = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')
else:
    timestamp = ''

if args.output == 'output':
    output_directory = pathlib.Path(args.output) / f'{input_dir.name}_{timestamp}' #if args.output is not None else pathlib.Path('output') / f'{input_dir.name}_{timestamp}'
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
    project_title=f'{input_dir.name}_{timestamp}'
else:
    project_title=''

out_dir, log_dir, processed_keywords_dir, doctext_dir, refs_dir, doctext_stemmed_dir, keyword_count_dir, results_dir, jsonfiles_dir = outdirtree_dict.values()

print(f"Output folder is: \n{out_dir}\n")

## 1.b) Read all files in input directory and select allowed filetypes

allowed_filetypes =  ['.pdf','.html','.mhtml','.doc','.docx'] # ['.doc','.docx'] # 

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
    keywords = pd.ExcelFile(args.keywords)
    keywords_path = args.keywords
else:    
    with rsrc.path("polmap", "keywords.xlsx") as res_path:
        keywords = pd.ExcelFile(res_path)
        keywords_path = res_path

    
 # if args.keywords is not None else pathlib.Path('keywords/keywords.xlsx')

sheets = keywords.sheet_names
print(f"Reading keywords dataset in {keywords_path}.\nSheets: {', '.join(sheets)}\n")

keywords = {sheet : keywords.parse(sheet) for sheet in sheets}
keywords_sheets = ['Target_keys', 'Goal_keys', 'MOI']

#remove all from stop_words to keep in keywords
stop_words = set(stopwords.words('english'))-set(['no','not','nor'])
stop_words.remove('all')

for sheet in keywords_sheets:
    keywords[sheet]['Keys'] = keywords[sheet]['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))
    keywords[sheet]['Keys'] = keywords[sheet]['Keys'].apply(lambda keywords: [plmp.preprocess_text(keyword, stop_words) for keyword in keywords.split(';')])
    #keywords[sheet].iloc[:,2:]=keywords[sheet].iloc[:,2:].applymap(lambda keyword: plmp.preprocess_text(str(keyword), stop_words))

countries = keywords['developing_countries']['Name'].values.tolist()
country_ls = []
for element in countries:
    element = [re.sub(r'[^a-zA-Z-]+', '', t.lower().strip()) for t in element.split()]
    # countries = [x.strip(' ') for x in countries]
    element = [stem(word) for word in element if not word in stop_words]
    element = ' '.join(element)
    country_ls.append(element)

keywords_destfilename = processed_keywords_dir / f'{project_title}_processed_{pathlib.Path(keywords_path).name}'

with pd.ExcelWriter(keywords_destfilename, engine='xlsxwriter') as _destfile:
    for sheetname in keywords_sheets:
        keywords[sheetname].to_excel(_destfile, sheet_name=sheetname)
    pd.DataFrame(country_ls,columns=['Name']).to_excel(_destfile, sheet_name='dev_countries_kwrds')

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
        print(exception)
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
    stemmed_text = re.sub(r'\n{1,}', ' ', stemmed_text)
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

target_col_names=['Policy', 'Target', 'Keyword', 'Count', 'Textlength']

target_ls = []
count_destfile_dict={}
##make the count
for policy, item in doc_texts.items():
    doc_target_ls =[]
    targetcount_filedest = keyword_count_dir / pathlib.PurePath(policy)
    targetcount_filedest.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
    targetcount_filedest = targetcount_filedest.parent / (targetcount_filedest.name.replace('.','_')+'.xlsx')
    count_destfile_dict[policy]=targetcount_filedest
    with pd.ExcelWriter(targetcount_filedest, mode='w', engine='openpyxl') as destfile: #replace with xlsx writer, make full target ls per document and save it
        for target, target_keyword_list in zip(keywords['Target_keys']['Target'],keywords['Target_keys']['Keys']): # range(0, len(keys['Keys'])):
            for keyword in target_keyword_list: #keywords['Target_keys'] #range(0,len(keys['Keys'][i])):
                counter = item['stemmed_text'].count(keyword)
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                if counter > 0:
                    row=[policy, target, keyword, counter, item['textlength']]
                    target_ls.append(row)
                    doc_target_ls.append(row)
                    #dfObj = dfObj.append(pd.Series(target_ls[-1], index=target_col_names), ignore_index=True)
                else:
                    continue
        dfObj= pd.DataFrame(doc_target_ls, columns=target_col_names)
        dfObj.to_excel(destfile, sheet_name='Target_raw_count')
        destfile.save()
    

target_df = pd.DataFrame(target_ls, columns=target_col_names)

count_destfile = results_dir / f'mapping_{project_title}.xlsx'

# with pd.ExcelWriter(count_destfile, engine='openpyxl') as _destfile:
#     target_df = pd.DataFrame(target_ls, columns=target_col_names)
#     target_df.to_excel(_destfile, sheet_name = 'Target_raw_count' )

writer = pd.ExcelWriter(count_destfile, engine='openpyxl')

print(f'Final results are stored in:\n{count_destfile}\n')

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
for policy, item in doc_texts.items():
    doc_goal_ls=[]
    with pd.ExcelWriter(count_destfile_dict[policy], mode='a', engine='openpyxl') as destfile:
        for goal, goal_keyword_list in zip(keywords['Goal_keys']['Goal'],keywords['Goal_keys']['Keys']):
            for keyword in goal_keyword_list:
                counter = item['stemmed_text'].count(keyword)
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                if counter > 0:
                    row=[policy, goal, keyword, counter, item['textlength']]
                    goal_ls.append(row)
                    doc_goal_ls.append(row)
                    #dfObj = dfObj.append(pd.Series(target_ls[-1], index=target_col_names), ignore_index=True)
                else:
                    continue
        dfObj = pd.DataFrame(doc_goal_ls, columns=goal_col_names)
        dfObj.to_excel(destfile, sheet_name='Goal_raw_count')
        destfile.save()
                

goal_df = pd.DataFrame(goal_ls, columns=goal_col_names)

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
moi_ls = []
##make the count
for policy, item in doc_texts.items():
    doc_moi_ls=[]
    with pd.ExcelWriter(count_destfile_dict[policy], mode='a', engine='openpyxl') as destfile:
        for moi, moi_keyword_list in zip(keywords['MOI']['Target'],keywords['MOI']['Keys']):
            for keyword in moi_keyword_list:
                if len(keyword) > 0:
                    counter = 0
                    sentence = item['stemmed_text']
                    word = str(keyword)
                    for match in re.finditer(word, sentence):
                        for element in country_ls:
                            #check for element 30 chars before match and until the end of the sentence
                            if element in sentence[match.start()-30:match.start()] or element in sentence[match.end():sentence.find('.',match.end())]:
                                word = word + ' ' + element
                                counter = counter + 1
                    #write counter together with target, policy, keyword as new row in df
                    #first write output to list
                    if counter > 0:
                        row = [policy, moi, word, counter, item['textlength']]
                        moi_ls.append(row)
                        doc_moi_ls.append(row)
        dfObj = pd.DataFrame(doc_moi_ls,columns=dev_countries_colnames)
        dfObj.to_excel(destfile, sheet_name='Dev_countries_raw_count')
        destfile.save()


moi_df = pd.DataFrame(moi_ls, columns=dev_countries_colnames)
moi_df.to_excel(writer, sheet_name='Dev_countries_raw_count')

with open(log_file, 'a') as f:
    f.write( 
        f'- {step+0.3}) Counting developing countries keywords in texts: {time.time()-start_time:.3e} seconds\n\n'
    )

#policies for which no keys were detected
detected_pol = moi_df['Policy'].tolist()

writer.save()


with open(log_file, 'a') as f:
    f.write( 
        f'- Total keywords counting time: {time.time()-start_count_time:.3e} seconds.'
        )

print(f'Step {step}: Counted keywords in texts.\n')
step += 1

# target_df.to_pickle("gd_target_df.pkl")
# goal_df.to_pickle("gd_goal_df.pkl")

######################################
########### 7) Postprocessing of keyword count

start_time = time.time()

target_df['Target'] = pspr.stringify_id(target_df['Target'])

results_dict = {}

#sdg_df=pspr.sdg_reference_df #MM we need to have that file available whenever running the script from other locations.
with rsrc.path("postprocess", "goal_target_list.xlsx") as res_path:
    sdg_df = pd.read_excel(res_path)

## 7.1) Aggregate count of keywords to target-level --> export this to final results workbook
results_dict['target_dat'] = pspr.aggregate_to_targets(target_df, sdg_df)

## 7.2) Filter out target counts based on number of counts, number of keywords and textlenght --> export this to final results workbook
results_dict['dat_filtered'] = pspr.filter_data(results_dict['target_dat'])

## 7.3) get overview on target-level --> export this to final results workbook
results_dict['target_overview_df'] = pspr.get_target_overview(results_dict['target_dat'], sdg_df)

## 7.4) get undetected targets --> export this to final results workbook
results_dict['undetected_targets'] = pspr.find_undetected_targets(results_dict['dat_filtered'], sdg_df)

## 7.5)  aggregate goal counts to goal-level --> export this to final results workbook
results_dict['goal_dat'] = pspr.aggregate_to_goals(goal_df, sdg_df) #MM What if no goals are detected? We need to handle this scenario

# 7.6) get goal_overview from target counts and goal counts --> export this to final results workbook
results_dict['goal_overview'] = pspr.get_goal_overview(results_dict['target_dat'], results_dict['goal_dat'], sdg_df)

# 7.7) group by document and aggregate to goals, when running this sheetname list  and sheetnames need to be adapted
results_dict['goals_grouped_by_document'] = pspr.group_byNAme_and_get_goaloverview(results_dict['target_dat'], results_dict['goal_dat'], sdg_df)

# 7.8) get goal overview but not with aggregated counts but with number of policies relating to a goal
results_dict['policies_per_goal'] = pspr.get_number_of_policies_per_goal(results_dict['target_dat'], results_dict['goal_dat'])

# # 7.9) get list of priorities
results_dict['priorities'] = pspr.map_pol_priorities(results_dict['target_dat'], sdg_df)


sheetnames_list = ['target_count', 'filtered_target_count', 'undetected_targets', 'goal_count', 'goal_overview', 'total_count_(goals_+_targets)', 'priorities']


# sheetnames_list = ['target_count', 'filtered_target_count', 'undetected_targets', 'goal_count', 'goal_overview', 'total_count_by_document', 'total_count']

# sheetnames = { df : sheetname for df, sheetname in zip(list(results_dict.keys()), sheetnames_list)}

# pprint.pprint(sheetnames)

mappingresults_destfile = results_dir / f'results_{project_title}.xlsx'

with pd.ExcelWriter(mappingresults_destfile, mode='w', engine='xlsxwriter') as destfile:
    for sheetname, df in results_dict.items():#zip( sheetnames.values()):

        #print(f'\n{} - {}')

        df.to_excel(destfile, sheet_name=sheetname)


with open(log_file, 'a') as f:
    f.write( 
        f'- Analyzing results and preparing summary tables: {time.time()-start_count_time:.3e} seconds.'
        )

print(f'Step {step}: Analyzed results and saved summary tables in {mappingresults_destfile}')
step += 1

######################################
########### 8) Create JSON files for visualization

# 8.1) create and export json files for bubblecharts on knowSDGs platform ## Fix this
sdg_bubbleplot_dict=pspr.create_json_files_for_bubbleplots(results_dict['target_overview_df'], results_dict['goal_overview'])
sdg_bubbles = jsonfiles_dir / 'sdg_bubbles.json'
with sdg_bubbles.open(mode='w', encoding='utf-8') as f:
    json.dump(sdg_bubbleplot_dict, f)


#To be moved somewhere in modules
pp_colors={'Human Development':'#F68D4A',
'Growth Jobs':'#FABE13',
'Green Deal':'#1A6835',
'Governance':'#005C95',
'Digitalisation':'#4D9CD5',
'Migration':'#DE6189',
'None':'#000000'
}

results_dict['priorities'].rename(columns = {'priority':'name', 'Count':'size'}, inplace = True)
results_dict['priorities']['goal_color']=results_dict['priorities']['name'].map(pp_colors)
pp_bubbleplot_dict= {'name': 'pp',
'children': list(results_dict['priorities'].to_dict('index').values())}
polprior_bubbles = jsonfiles_dir / 'polprior_bubbles.json'
with polprior_bubbles.open(mode='w', encoding='utf-8') as f:
    json.dump(pp_bubbleplot_dict, f)

print(jsonfiles_dir)

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

