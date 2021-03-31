import argparse, pathlib, re, logging
from nltk import translate
import pandas as pd
import datetime as dt
import googletrans as ggltrns
from pygoogletranslation import Translator

parser = argparse.ArgumentParser(description="""Expands and saves an excel file of keywords for sdg goals and targets.
The excel fil must have multiple sheets named as following:
'Target_keys' for SDG targets, 'Goal_keys' for SDG Goals, 'MOI' for developing countris specific targets, 'developing_countries' for acronims and nouns of developing countries
Each Sheet must have a (the first) column named 'Target'/'Goal' containing the names/identifiers of the SDG goal or target,
and a (the second) column named 'Keys'where the keys are stored in a single cell each separated by a semicolon (;).
""")
parser.add_argument('-i', '--input', help='Input directory', default='input')
parser.add_argument('-o', '--output', help='Output directory', default='keywords')
parser.add_argument('-at', '--add_timestamp', help='Add a timestamp to output directory', type=bool, default=True)

#parser.add_argument('-l', '--language', help='Select translation language', default='it')

args = parser.parse_args()

#def func
keywords = pd.ExcelFile(args.input) # 'keywords/keywords.xlsx'
filename = pathlib.Path(args.input).stem
timestamp =  dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

if args.add_timestamp is not None:
    filename += f'_{timestamp}'

output = pathlib.Path(args.output) / f'{filename}.xlsx'
log_file = pathlib.Path(args.output) / f'{filename}.log'
print_file = pathlib.Path(args.output) / f'{filename}_out.txt' 
log_file.touch(mode=0o666)
logging.basicConfig(filename=log_file, filemode='a', level=logging.WARNING)

#sheets = a list of sheets where keywords are
#keys_df = [keywords.parse(sheet) for sheet in sheets]
keys_dfs = [keywords.parse('Target_keys'), keywords.parse('Goal_keys'), keywords.parse('MOI')]

for df in keys_dfs:
    df['Keys']=df['Keys'].apply(lambda keywords: re.sub(';$', '', keywords))
    df['Keys']=df['Keys'].apply(lambda keywords: re.sub(';;', ';', keywords))
    #df['Keys']=df['Keys'].apply(lambda keywords: re.sub(r'[^a-zA-Z0-9; -.]+', ';', keywords))

keys_dfs.append(keywords.parse('developing_countries'))

target_keys, goal_keys, devco_keys, devco_names = keys_dfs


target_dict = {}
goal_dict = {}
devco_dict = {}

for id, target in zip(target_keys['Target'], target_keys['Keys']):
    target_dict[id] = [key.lstrip() for key in target.split(';')]

for id, target in zip(goal_keys['Goal'], goal_keys['Keys']):
    goal_dict[id] = [key.lstrip() for key in target.split(';')]

for id, target in zip(devco_keys['Target'], devco_keys['Keys']):
    devco_dict[id] = [key.lstrip() for key in target.split(';')]    

ggl_translator = ggltrns.Translator()

translator = Translator(retry=3, sleep=5)

sdg_dictionaries = {'target' : target_dict, 'goal' : goal_dict, 'devco' : devco_dict} # 'devco_names' : devco_names}

# for sheet_name, sdg_dict in sdg_dictionaries.items():
#     for id, target in sdg_dict.items():
#         try:
#             translated_keys = (translator.translate(target, dest='it'))
#             sdg_dict[id] = [key.text for key in translated_keys] # for key in target]
#             print(f'{sheet_name}, {id} - {translated_keys}
#         except Exception as exception:
#                 translated_key = 'WARNING! : Translation Failed'
#                 sdg_dict[id].append('ERRORE: Traduzione fallita')
#                 print(f'{sheet_name}, {id}, {count}, {key}, {translated_key}', exception)
#                 logging.exception(f'{sheet_name}, {id}, {count}, {key} raised exception: \n{exception} \n\n')

consolle_out = []

for sheet_name, sdg_dict in sdg_dictionaries.items():
    for id, target in sdg_dict.items():
        #sdg_dict[id] = [translator.translate(key, dest='it').text for key in target]
        sdg_dict[id] = []
        for count, key in enumerate(target):
            try:
                translated_key = translator.translate(key, src='en', dest='it').text
                translated_key = re.sub('[ .]+$', '', translated_key)
                sdg_dict[id].append(translated_key)
                consolle_out.append(f'\n{sheet_name}, {id}, {count} -\n{key} :\t {translated_key}')
            except Exception as exception:
                translated_key = 'WARNING! : Translation Failed'
                sdg_dict[id].append('ERRORE: Traduzione fallita')
                consolle_out.append(f'\n{sheet_name}, {id}, {count}, {key}, {translated_key}')
                logging.exception(f'{sheet_name}, {id}, {count}, {key} raised exception: \n{exception} \n\n')
            # print(f'\n\n{count}\t{key}:\n{translator.translate(key, dest='it').text}')
        #sdg_dict[id] = [translator.translate(key, dest='it').text for key in target]

with open(print_file, 'w') as _file:
    _file.writelines(consolle_out)

# for sheet_name, sdg_dict in sdg_dictionaries.items():
#     for id, target in sdg_dict.items():
#         sdg_dict[id] = ';'.join(target)

target_df = pd.DataFrame.from_dict(target_dict, orient ='index') 
goal_df = pd.DataFrame.from_dict(goal_dict, orient ='index')
devco_df = pd.DataFrame.from_dict(devco_dict, orient ='index')

#merge df and return

with pd.ExcelWriter(output, engine='xlsxwriter') as writer: # 'keywords_copy_for_transaltion.xlsx'
    target_df.to_excel(writer, sheet_name='Target_keys')
    goal_df.to_excel(writer, sheet_name='Goal_keys')
    devco_df.to_excel(writer, sheet_name='MOI')
    devco_names.to_excel(writer, sheet_name='developing_countries')