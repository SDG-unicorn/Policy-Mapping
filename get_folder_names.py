import io, csv, re, os, json
from os import listdir
import pandas as pd

path = os.getcwd()+str("\\pdf_re\\Final_Run_Old_Clean\\")
# path = os.getcwd()+str("\\pdf_re\\pdf\\")
folders = [folder for folder in listdir(path)]



df = pd.DataFrame(folders)

df.to_excel("folder_list.xlsx", sheet_name="Policy_Names")


