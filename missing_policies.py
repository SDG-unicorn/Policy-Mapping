import io, csv, re, os, json
from os import listdir
from os.path import isfile, join
from nltk.corpus import stopwords
import pandas as pd




detected_pol = pd.read_excel('detected_pol.xlsx', sheet_name= 'list' )

#check for colname
#print(list(detected_pol))

#write to list
#policies for which no keys were detected
detected_pol = detected_pol['unique(dat_count$Policy)'].tolist()


####### read in pdf
##go into folder of 1 policy and read in all docs
path = os.getcwd()+str("\\pdf_re\old_policies\\")
# path = os.getcwd()+str("\\pdf_re\\pdf\\")
pol_ls = [folder for folder in listdir(path)]


#make list with policies not detected
undet_pol = [x for x in pol_ls if x not in detected_pol]

undet_pol = pd.Series(undet_pol)

undet_pol.to_excel('missing_policies.xlsx', sheet_name='RAW')

