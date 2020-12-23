import io, csv, re, os, json
from os import listdir
from os.path import isfile, join
import pandas as pd
import xlsxwriter
import time




path = os.getcwd()+str("\\pdf_re\\Final_Run\\")
# path = os.getcwd()+str("\\pdf_re\\pdf\\")
folders = [folder for folder in listdir(path)]

final_ls = []
for item in folders:
    temp_path = path + str(item)
    files = [file for file in listdir(temp_path) if isfile(join(temp_path, file))]
    if len(files) > 0:
        file_path_ls = []
        for doc in files:
            file_path = temp_path + "\\" + str(doc)
            file_path_ls.append(file_path)
    temp_file_paths = ' ; '.join(file_path_ls)
    #make list comprehension removing .pdf from files
    files = [file[:-4] for file in files]
    temp_files = ' ; '.join(files)
    final_ls.append(tuple((item, temp_files, temp_file_paths)))

final_df = pd.DataFrame(final_ls, columns =['Policy', 'Document Codes', 'Filepaths'])

final_df.to_excel("document_codes.xlsx", sheet_name="Overview")
