import pandas as pd
import ast
from pathlib import Path
#import .processed_keywords

script_dir = Path( __file__ ).parent

#Load excel file with processed keywords
prockeys = pd.ExcelFile(script_dir / 'processed_keywords' / 'processed_keywords.xlsx')
sheets = prockeys.sheet_names
prockeys = {sheet : prockeys.parse(sheet) for sheet in sheets}
for sheet in prockeys.keys():
    if sheet in ['Target_keys', 'Goal_keys', 'MOI']:
        prockeys[sheet]['Keys'] = prockeys[sheet]['Keys'].apply(ast.literal_eval) #Convert string represetion of list into list

#Unit test: load processed_keywords and compare md5sum strin with md5sum of source file, if equal pass test.
#Purpose: Check that keywords are updated or not corrupted.

indicators = pd.read_excel(script_dir / 'indicators.xlsx')
indicators['UN_Indicators'] = indicators['UN_Indicators'].apply(lambda x: ast.literal_eval(x))

