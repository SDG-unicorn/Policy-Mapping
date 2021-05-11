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
parser.add_argument('-at', '--add_timestamp', help='Add a timestamp to output directory', type=bool, default=False)

args = parser.parse_args()

#def func
keywords = pd.ExcelFile(args.input) # 'keywords/keywords.xlsx'
filename = pathlib.Path(args.input).stem
timestamp =  dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

if args.add_timestamp is not None:
    filename += f'_{timestamp}'

output = pathlib.Path(args.output) / f'{filename}_collapsed.xlsx'


#sheets = a list of sheets where keywords are
#keys_df = [keywords.parse(sheet) for sheet in sheets]
keys_dfs = [keywords.parse('Target_keys'), keywords.parse('Goal_keys'), keywords.parse('MOI')]


for index, df in enumerate(keys_dfs):
    #temp_out = pathlib.Path(args.output) / f'{filename}_temp_{index}.xlsx'
    #if translate exectule lines below

    col_df=df.iloc[:, 2:].fillna(value=False)
    col_df=col_df.apply(lambda x: list(filter(None, x)), axis=1)
    #col_df=col_df.apply(lambda x: filter(None, x))
    #print(col_df)
    col_df=col_df.apply(lambda x: ";".join(map(str, x)))
    # col_df=col_df.str.replace('nan', '')
    # col_df=col_df.apply(lambda keywords: re.sub(r', ,', '', str(keywords)))
    # col_df=col_df.apply(lambda keywords: re.sub(r' {2,}', '', str(keywords)))
    # col_df=col_df.str.replace("', '", ";")
    # col_df=col_df.str.replace("', ","")
    # col_df=col_df.apply(lambda keywords: re.sub(r"\['|'\]|\]", '', str(keywords)))
    #col_df.to_excel(temp_out, engine='xlsxwriter')
    col_df.rename('Keys', inplace=True)
    lab_df=df.iloc[:, 1]
    keys_dfs[index] = pd.merge(lab_df, col_df, right_index = True,
               left_index = True)
    #df['Keys']=df['Keys'].apply(lambda keywords: re.sub(r'[^a-zA-Z0-9; -.]+', ';', keywords))

keys_dfs.append(keywords.parse('developing_countries'))

target_df, goal_df, devco_df, devco_names = keys_dfs

with pd.ExcelWriter(output, engine='xlsxwriter') as writer: # 'keywords_copy_for_transaltion.xlsx'
    target_df.to_excel(writer, sheet_name='Target_keys')
    goal_df.to_excel(writer, sheet_name='Goal_keys')
    devco_df.to_excel(writer, sheet_name='MOI')
    devco_names.to_excel(writer, sheet_name='developing_countries')