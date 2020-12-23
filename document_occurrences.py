import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import time


####### read in pdf
##go into folder of 1 policy and read in all docs
path = os.getcwd()+str("\\pdf_re\\Final_Run_UPDATE\\")
#create list with all folders
folders = [folder for folder in listdir(path)]


#empty list where tuples will be appended
df_ls = []
empty_folders = []
for item in folders:
    #name of the folder
    print(item)
    #path to the folder
    temp_path = path + str(item)
    #get all files inside a folder as a list
    files = [file for file in listdir(temp_path) if isfile(join(temp_path, file))]
    #check if folders are emptym
    if len(files) > 0:
        # go through file list and create tuple for each file + respective folder name
        for pdf_item in files:
            temp_tuple = (pdf_item, item)
            #appen tuple to list
            df_ls.append(temp_tuple)
    else:
        empty_folders.append(item)

f=open('empty_folders.txt','w')
for ele in empty_folders:
    f.write(ele+'\n')
f.close()

#make final dataframe from tuple list
df = pd.DataFrame(df_ls, columns =['Document_File', 'Foldername'])
#group by files and concatenate folder names to see in which folders same files have been used
df = df.groupby('Document_File')['Foldername'].apply(';'.join).to_frame().reset_index()

#add new column to count in how many folders the document is used
df["Count"] = ""

#loop over df and count
for index, row in df.iterrows():
    row["Count"] = row['Foldername'].count(';') + 1

#sort descending
df = df.sort_values(by='Count', ascending=False)
#reset index for export
df = df.reset_index(drop=True)


folders_df = pd.DataFrame(folders)

#write to excel
date = time.strftime("%d%m%Y")
writer = pd.ExcelWriter(os.getcwd() + str("\\pdf_re\\folder_list_") + str(date) + str(".xlsx"), engine='xlsxwriter')

#export final output
folders_df.to_excel(writer, sheet_name='folder_list')
df.to_excel(writer, sheet_name='multipurpose_docs')

writer.save()
