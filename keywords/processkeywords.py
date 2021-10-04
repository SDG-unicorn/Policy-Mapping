import argparse, re, pathlib, sys

import pandas as pd
from nltk.corpus import stopwords

sys.path.insert(0, str(pathlib.Path.cwd().parent))
import polmap as plmp


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="""Read keywords from an excel file, apply preprocessing steps, save the results for mappings.""")
    parser.add_argument('-i', '--input', help='Input file', default='keywords.xlsx')
    parser.add_argument('-o', '--output', help='Output file', default='processed_keywords/processed_keywords.xlsx')
    args = parser.parse_args()
    input_file, ouput_file = pathlib.Path(args.input), pathlib.Path(args.output)

def processkeywords(input_file):
    """
    Preprocess keywords from a multisheet excel file.
    The excel file must have 'Target_keys', 'Goal_keys', 'MOI' sheets.
    Each sheet must have a column named 'Keys' where keywords are stored as a strings separated by a ';'.
    """
    keywords = pd.ExcelFile(input_file)
    sheets = keywords.sheet_names
    print(f"Reading keywords dataset in {input_file}.\nSheets: {', '.join(sheets)}\n")

    keywords = {sheet : keywords.parse(sheet) for sheet in sheets}
    keywords_sheets = ['Target_keys', 'Goal_keys', 'MOI']

    #remove all from stop_words to keep in keywords
    stop_words = set(stopwords.words('english'))-set(['no','not','nor'])
    stop_words.remove('all')

    for sheet in keywords_sheets:
        keywords[sheet]['Keys'] = keywords[sheet]['Keys'].apply(lambda keywords: re.sub(';$', '', str(keywords)))
        keywords[sheet]['Keys'] = keywords[sheet]['Keys'].apply(lambda keywords: [plmp.preprocess_text(str(keyword), stop_words) for keyword in keywords.split(';')])
        
    # countries = keywords['developing_countries']['Name'].values.tolist()
    # country_ls = []
    # for element in countries:
    #     element = [re.sub(r'[^a-zA-Z-]+', '', t.lower().strip()) for t in element.split()]
    #     # countries = [x.strip(' ') for x in countries]
    #     element = [stem(word) for word in element if not word in stop_words]
    #     element = ' '.join(element)
    #     country_ls.append(element)


    # with open(log_file, 'a') as f:
    #     f.write( 
    #         f'{step}) Reading and preprocessing keywords in {keywords_path} file: {time.time()-start_time:.3e} seconds\n\n'
    #     )

    print(f'Read and processed keywords')
    return keywords   

if __name__=="__main__":# if md5sum of input file is different for md5sum stored in processed keywords.
    keywords = processkeywords(input_file)
    with pd.ExcelWriter(ouput_file, engine='xlsxwriter') as _destfile:
        for sheetname in keywords.keys():
            keywords[sheetname].to_excel(_destfile, sheet_name=sheetname)
        #pd.DataFrame(country_ls,columns=['Name']).to_excel(_destfile, sheet_name='dev_countries_kwrds')
