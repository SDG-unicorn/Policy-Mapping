import argparse, re, pathlib, os, time, sys, hashlib

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
    print(f"Reading keywords dataset in {input_file}.\n\nSheets: {', '.join(sheets)}\n")

    keywords_sheets = ['Target_keys', 'Goal_keys', 'MOI']
    keywords = {sheet : keywords.parse(sheet) for sheet in sheets if sheet in keywords_sheets}    

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

    # Both the variables would contain time 
    # elapsed since EPOCH in float
    ti_c = os.path.getctime(input_file)
    ti_m = os.path.getmtime(input_file)
    
    # Converting the time in seconds to a timestamp
    ti_c = time.strptime(time.ctime(ti_c))
    ti_m = time.strptime(time.ctime(ti_m))
  
    # Transforming the time object to a timestamp 
    # of ISO 8601 format
    ti_c = time.strftime("%Y-%m-%d_T%H:%M:%S", ti_c)
    ti_m = time.strftime("%Y-%m-%d_T%H:%M:%S", ti_m)

    with open(input_file, "rb") as file_to_check:
        # read contents of the file
        data = file_to_check.read()    
        # pipe contents of the file through
        md5_returned = hashlib.md5(data).hexdigest()
    
    metadata = {'File' : str(input_file.name),
                'Path' : str(input_file.resolve()),
                'Created' : str(ti_c),
                'Modified' : str(ti_m),
                'MD5 hash' : str(md5_returned)}

    metadata = pd.DataFrame.from_dict({'Fields': metadata.keys(), 'Values': metadata.values()})

    keywords = processkeywords(input_file)
    with pd.ExcelWriter(ouput_file, engine='xlsxwriter') as _destfile:
        metadata.to_excel(_destfile, sheet_name='Metadata', index=False)
        for sheetname in keywords.keys():
            keywords[sheetname].iloc[:, 0:2].to_excel(_destfile, sheet_name=sheetname, index=False)        
        #pd.DataFrame(country_ls,columns=['Name']).to_excel(_destfile, sheet_name='dev_countries_kwrds')

    # Import hashlib library (md5 method is part of it)
# import hashlib
# # File to check
# file_name = 'filename.exe'
# # Correct original md5 goes here
# original_md5 = '5d41402abc4b2a76b9719d911017c592'  
# # Open,close, read file and calculate MD5 on its contents 
# with open(file_name) as file_to_check:
#     # read contents of the file
#     data = file_to_check.read()    
#     # pipe contents of the file through
#     md5_returned = hashlib.md5(data).hexdigest()
# # Finally compare original MD5 with freshly calculated
# if original_md5 == md5_returned:
#     print "MD5 verified."
# else:
#     print "MD5 verification failed!."
