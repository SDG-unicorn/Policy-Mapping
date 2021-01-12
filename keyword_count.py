import io, csv, re, os, json
from os import listdir #MM I would use pathlib insted of os, so that we can make path definition os independent
from os.path import isfile, join
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
from nltk.tokenize import word_tokenize
from whoosh.lang.porter import stem
from nltk.stem import WordNetLemmatizer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import xlsxwriter
from itertools import chain
##MM imports
import datetime as dt
import pathlib
import logging


########### MM 1) Define global variables like time, input_dir, ouput_dirs

#def make_directories(project='TEI'): #MM start func definition
date = dt.datetime.now().date().isoformat()
time = dt.datetime.now().time().isoformat(timespec='seconds').replace(':', '')
current_date = '_'+date+'_T'+time

project_title = 'TEI'+str(current_date) #TEI shall be replace with project string varible provided by the user

#try
out_dir = pathlib.Path.cwd() / 'output' / project_title 
log_dir = out_dir / 'logs'
results_dir = out_dir / 'results'

dir_dict = { directory: directory.mkdir(mode=0o777, parents=True, exist_ok=True) for directory in [out_dir, log_dir, results_dir] } #Set exist_ok=False later on
#except FileExistsError, Error : #MM Deal with cases where directory creation failed. Error occurring here will not be catched in the log.

#return #MM end func 

####### Create logfile for current run.

log_file = log_dir / 'mapping_{}.log'.format(project_title)
log_file.touch(mode=0o666)
logging.basicConfig(filename=log_file, filemode='a', level=logging.WARNING)

####### Read all files in input directory and select allowed filetypes

input_dir = pathlib.Path.cwd() / 'pdf_re' / 'TEI' #MM let user provide an input dir
input_folder_name = input_dir.name

allowed_filetypes=['.pdf','.html','.mhtml','.doc','.docx']

files = sorted(input_dir.glob('**/*.pdf'))
files = [ file for file in files if file.suffix in allowed_filetypes]
#MM assert files==False and log assertion error.

######################################

########### 2) read in all keywords #MM this could be moved below after the pdf conversion and before the counting, to have a little bit more of a flow:
#e.g. 1) create global variable, 2) convert doc to text 3) load keywords, lemmatize keywords and text, 4) count keys in text 5) save output

keys = pd.read_excel('keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'Sheet1' )

##read in 1 row with keys per target
## split row by ; - series of list of strings

keys['Keys'] = keys['Keys'].str.split(pat = ";")

##process words - remove stopwords, stemming, lemmatizing

#set stop words
stop_words = set(stopwords.words("english"))
#remove all from stop_words to keep in keywords
stop_words.remove("all")

# lemmatizer = WordNetLemmatizer()
for i in range(0, len(keys['Keys'])):
    for j in range(0,len(keys['Keys'][i])):
        # keys['Keys'][i][j] = word_tokenize(keys['Keys'][i][j])
        keys['Keys'][i][j] = [re.sub(r"[^a-zA-Z-]+", '', t.lower().strip()) for t in keys['Keys'][i][j].split()]
        #add whitespaces to words
        keys['Keys'][i][j] = [word.center(len(word)+2) for word in keys['Keys'][i][j]]
        #transform rd back to R&D for later detection
        keys['Keys'][i][j] = [w.replace(" rd ", "R&D") for w in keys['Keys'][i][j]]
        #remove words > 2
        keys['Keys'][i][j] = [word for word in keys['Keys'][i][j] if len(word) > 2 or word == "ph"]
        # remove '
        # keys['Keys'][i][j] = [s.replace('\'', '') for s in keys['Keys'][i][j]]
        # remove whitespaces
        keys['Keys'][i][j] = [x.strip(' ') for x in keys['Keys'][i][j]]
        # add special char to prevent aids from being stemmed to aid
        keys['Keys'][i][j] = [w.replace("aids", "ai&ds&") for w in keys['Keys'][i][j]]
        keys['Keys'][i][j] = [w.replace("productivity", "pro&ductivity&") for w in keys['Keys'][i][j]]
        keys['Keys'][i][j] = [w.replace("remittances", "remit&tance&") for w in keys['Keys'][i][j]]
        #stem words
        keys['Keys'][i][j] = [stem(word) for word in keys['Keys'][i][j] if not word in stop_words if word != "aids"]
        # remove special char for detection in text
        keys['Keys'][i][j] = [w.replace("ai&ds&", "aids") for w in keys['Keys'][i][j]]
        keys['Keys'][i][j] = [w.replace("pro&ductivity&", "productivity") for w in keys['Keys'][i][j]]
        keys['Keys'][i][j] = [w.replace("remit&tance&", "remittance") for w in keys['Keys'][i][j]]
        # lemmatizing words
        # keys['Keys'][i][j] = [lemmatizer.lemmatize(word) for word in keys['Keys'][i][j] if not word in stop_words]
        #merge back together to 1 string
        keys['Keys'][i][j] = ' '.join(keys['Keys'][i][j])
        #add leading and trailing whitespace
        keys['Keys'][i][j] = " " + keys['Keys'][i][j] + " "

######################################

########### 3) Read pdf files and convert them into text 
##create class for PDFMining
###use PDF miner
class PdfConverter:
   def __init__(self, file_path):
       self.file_path = file_path
# convert pdf file to a string which has space among words
   def convert_pdf_to_txt(self):
       rsrcmgr = PDFResourceManager()
       retstr = StringIO()
       laparams = LAParams()
       logging.propagate = False
       logging.getLogger().setLevel(logging.ERROR)
       device = TextConverter(rsrcmgr, retstr, laparams=laparams)
       fp = open(self.file_path, 'rb')
       interpreter = PDFPageInterpreter(rsrcmgr, device)
       password = ""
       maxpages = 0
       caching = True
       pagenos = set()
       for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
           interpreter.process_page(page)
       fp.close()
       device.close()
       str = retstr.getvalue()
       retstr.close()
       return str

PDFtext = []
counter = 0
for pdf_item in files:
    print(pdf_item)
    counter += 1
    try:
        policy_texts = [] # def pdf_to_text (pdf_file): #MM this should be turned into the body of a function that gets a pdf file and returns the text of it.
        pdfConverter = PdfConverter(file_path=pdf_item) 
        policy_texts.append(pdfConverter.convert_pdf_to_txt())
        pdf_item_name='/'.join(pdf_item.parts[pdf_item.parts.index(input_dir.name)+1:]) #the path string of each file, including all parent directories except that are subdirectories of the input directory. It basically capture the directory tree 
        PDFtext.append([pdf_item_name,' ; '.join(policy_texts)])
    except Exception as excptn: #MM I'd log errors as described in https://realpython.com/python-logging/, we need to test this.
        logging.exception('{doc_file} raised exception {exception} \n'.format(doc_file=pdf_item.name, exception=excptn))

#print(PDFtext)
print("Number of docs: ", len(PDFtext))
print("Number of folders: ", counter)

lemmatizer = WordNetLemmatizer()
for item in PDFtext:
    #detect soft hyphen that separates words
    item[1] = item[1].replace('.', ' .')
    item[1] = [re.sub(r'-\n', '', t) for t in item[1].split()]
    #get indices of soft hyphens
    indices = [i for i, s in enumerate(item[1]) if '\xad' in s]
    #merge the separated words
    for index in indices:
        item[1][index] = item[1][index].replace('\xad', '')
        item[1][index+1] = item[1][index]+item[1][index+1]
    #remove unnecessary list elements
    for index in sorted(indices, reverse=True):
        del item[1][index]
    #remove special character, numbers, lowercase
    item[1] = [re.sub(r"[^a-zA-Z-\.]+", '', t.lower().strip()) for t in item[1]]
    #add whitespaces
    item[1] = [word.center(len(word)+2) for word in item[1]]
    #recover R&D for detection
    item[1] = [w.replace(" rd ", "R&D") for w in item[1]]
    # remove words > 2
    item[1] = [word for word in item[1] if len(word) > 2 or word == "ph"]
    # remove '
    # item[1] = [s.replace('\'', '') for s in item[1]]
    #remove whitespaces
    item[1] = [x.strip(' ') for x in item[1]]
    #add special char to prevent aids from being stemmed to aid
    item[1] = [w.replace("aids", "ai&ds&") for w in item[1]]
    item[1] = [w.replace("productivity", "pro&ductivity&") for w in item[1]]
    item[1] = [w.replace("remittances", "remit&tance&") for w in item[1]]
    item[1] = [w.replace("remittance", "remit&tance&") for w in item[1]]
    print(item[1])
    # stem words
    item[1] = [stem(word) for word in item[1] if not word in stop_words]
    #remove special char for detection in text
    item[1] = [w.replace("ai&ds&", "aids") for w in item[1]]
    item[1] = [w.replace("pro&ductivity&", "productivity") for w in item[1]]
    item[1] = [w.replace("remit&tance&", "remittance") for w in item[1]]
    #try lemmatizing
    # item[1] = [lemmatizer.lemmatize(word) for word in item[1] if not word in stop_words]
    # merge back together to 1 string
    item[1] = ' '.join(item[1])
    #add trailing leading whitespace
    item[1] = " " + item[1] + " "
    item = item.append(len(item[1]))


##make list pandas df and export to check intermediately
# Create the pandas DataFrame
df = pd.DataFrame(PDFtext, columns = ['Policy', 'Text', 'Textlength'])
#no point in exporting since excel cuts off text after char len >32767
#change directory respectively
res_df_name = results_dir / 'polmap_transformation_out_{}.xlsx'.format(project_title)
df.to_excel(res_df_name, sheet_name="RAW") 
#MM here we could parametrize also the project (TEI) by using str("mystr_{project}_{date}.xlsx).format(project=my_project, date=current_date)

################################

final_ls = []
##make the count
for item in PDFtext:
    for i in range(0, len(keys['Keys'])):
        for j in range(0,len(keys['Keys'][i])):
            # print(keys['Keys'][i][j])
            counter = item[1].count(str(keys['Keys'][i][j]))
            #write counter together with target, policy, keyword as new row in df
            #first write output to list
            final_ls.append([item[0], keys['Target'][i], keys['Keys'][i][j], counter, len(item[1])])

final_df = pd.DataFrame(final_ls, columns=['Policy', 'Target', 'Keyword', "Count", "Textlength"])

#drop rows where keyword = ""
# print(len(final_df['Target']))
final_df = final_df[final_df.Keyword != ""]
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
final_df = final_df[final_df.Count != 0]
# print(len(final_df['Target']))

# Create a Pandas Excel writer using XlsxWriter as the engine.

write_name = results_dir / 'mapping_{}.xlsx'.format(project_title)
writer = pd.ExcelWriter(write_name, engine='xlsxwriter')
#SB writer = pd.ExcelWriter(os.getcwd()+str("\\results\\raw\\mapping_TEI_{}.xlsx").format(current_date), engine='xlsxwriter')

#export final output
final_df.to_excel(writer, sheet_name='RAW')

#############################

##county names

countries_in = pd.read_excel('keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'developing_countries')
countries = countries_in['Name'].values.tolist()
country_ls = []
for element in countries:
    element = [re.sub(r"[^a-zA-Z-]+", '', t.lower().strip()) for t in element.split()]
    # countries = [x.strip(' ') for x in countries]
    element = [stem(word) for word in element if not word in stop_words]
    element = ' '.join(element)
    country_ls.append(element)

##specific subset of relevant targets
dev_count_keys = pd.read_excel('keys_from_RAKE-GBV_DB_SB_v3.xlsx', sheet_name= 'Sheet2' )

#split keys
dev_count_keys['Keys'] = dev_count_keys['Keys'].str.split(pat = ";")

#apply simple text processing steps
for i in range(0, len(dev_count_keys['Keys'])):
    for j in range(0,len(dev_count_keys['Keys'][i])):
        # dev_count_keys['Keys'][i][j] = word_tokenize(dev_count_keys['Keys'][i][j])
        dev_count_keys['Keys'][i][j] = [re.sub(r"[^a-zA-Z-]+", '', t.lower().strip()) for t in dev_count_keys['Keys'][i][j].split()]
        #add whitespaces to words
        dev_count_keys['Keys'][i][j] = [word.center(len(word)+2) for word in dev_count_keys['Keys'][i][j]]
        #transform rd back to R&D for later detection
        dev_count_keys['Keys'][i][j] = [w.replace(" rd ", "R&D") for w in dev_count_keys['Keys'][i][j]]
        #remove words > 2
        dev_count_keys['Keys'][i][j] = [word for word in dev_count_keys['Keys'][i][j] if len(word) > 2 or word == "ph"]
        # remove '
        # dev_count_keys['Keys'][i][j] = [s.replace('\'', '') for s in dev_count_keys['Keys'][i][j]]
        # remove whitespaces
        dev_count_keys['Keys'][i][j] = [x.strip(' ') for x in dev_count_keys['Keys'][i][j]]
        # add special char to prevent aids from being stemmed to aid
        dev_count_keys['Keys'][i][j] = [w.replace("aids", "ai&ds&") for w in dev_count_keys['Keys'][i][j]]
        #stem words
        dev_count_keys['Keys'][i][j] = [stem(word) for word in dev_count_keys['Keys'][i][j] if not word in stop_words if word != "aids"]
        # remove special char for detection in text
        dev_count_keys['Keys'][i][j] = [w.replace("ai&ds&", "aids") for w in dev_count_keys['Keys'][i][j]]
        # lemmatizing words
        # dev_count_keys['Keys'][i][j] = [lemmatizer.lemmatize(word) for word in dev_count_keys['Keys'][i][j] if not word in stop_words]
        #merge back together to 1 string
        dev_count_keys['Keys'][i][j] = ' '.join(dev_count_keys['Keys'][i][j])
        #add trailing and leading whitespace
        dev_count_keys['Keys'][i][j] = " " + dev_count_keys['Keys'][i][j] + " "


#make final count

final_ls = []
##make the count
for item in PDFtext:
    for i in range(0, len(dev_count_keys['Keys'])):
        for j in range(0,len(dev_count_keys['Keys'][i])):
            if len(dev_count_keys['Keys'][i][j]) > 0:
                counter = 0
                sentence = item[1]
                word = str(dev_count_keys['Keys'][i][j])
                for match in re.finditer(word, sentence):
                    for element in country_ls:
                        #check for element 30 chars before match and until the end of the sentence
                        if element in sentence[match.start()-30:match.start()] or element in sentence[match.end():sentence.find('.',match.end())]:
                            word = word + " " + element
                            counter = counter + 1
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                if counter != 0:
                    final_ls.append([item[0], dev_count_keys['Target'][i], word, counter, len(item[1])])

final_df = pd.DataFrame(final_ls, columns=['Policy', 'Target', 'Keyword', "Count", "Textlength"])

#drop rows where keyword = ""
# print(len(final_df['Target']))
final_df = final_df[final_df.Keyword != ""]
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
final_df = final_df[final_df.Count != 0]
# print(len(final_df['Target']))

#export final output
final_df.to_excel(writer, sheet_name='RAW_dev_countries')

#policies for which no keys were detected
detected_pol = final_df['Policy'].tolist()

writer.save()

