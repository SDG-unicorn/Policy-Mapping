import os
import pandas as pd
import re
import shutil

file_names = pd.read_excel('Policy_list_right.xlsx', sheet_name='for_Diego_1')

policy_ls = file_names['Name'].values.tolist()
file_names['NewNameSuggestions'] = file_names.NewNameSuggestions.astype(str)
temp_ls = file_names['NewNameSuggestions'].values.tolist()


clean_policy_names = temp_ls + policy_ls
clean_policy_names = [x.strip() for x in clean_policy_names]
clean_policy_names = [x for x in clean_policy_names if x is not None]
clean_policy_names = [x.lower() for x in clean_policy_names]
clean_policy_names = [re.sub(r'[^A-Za-z0-9 ]+', '', x) for x in clean_policy_names]

folder_names = os.listdir("D:\\Work_JRC\\Mapping_2\\\pdf_re\\Final_Run_Old_Clean")
clean_folder_names = folder_names
clean_folder_names = [x.strip() for x in clean_folder_names]
clean_folder_names = [x.lower() for x in clean_folder_names]
clean_folder_names = [re.sub(r'[^A-Za-z0-9 ]+', '', x) for x in clean_folder_names]

##get new policies
new_policies = [x for x in clean_folder_names if x not in clean_policy_names]

indices = []
for item in new_policies:
    indices.append(clean_folder_names.index(item))

#delete all files in specific folder
for item in indices:
    folder = str("D:\\Work_JRC\\Mapping_2\\\pdf_re\\Final_Run_Old_Clean\\"+folder_names[item])
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    #delete empty folders
    os.rmdir(folder)

