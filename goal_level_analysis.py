import io, csv, re, os, json
from os import listdir
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
import logging
import xlsxwriter
from itertools import chain
import xlsxwriter
from itertools import chain

###########read in all keywords

keys = pd.read_excel('keys_goal_level_GBV.xlsx', sheet_name= 'SDGs' )

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
        keys['Keys'][i][j] = [re.sub(r"/[^a-zA-Z0-9 ]/g", '', t.lower().strip()) for t in keys['Keys'][i][j].split()]
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
        #stem words
        keys['Keys'][i][j] = [stem(word) for word in keys['Keys'][i][j] if not word in stop_words if word != "aids"]
        # lemmatizing words
        # keys['Keys'][i][j] = [lemmatizer.lemmatize(word) for word in keys['Keys'][i][j] if not word in stop_words]
        #merge back together to 1 string
        keys['Keys'][i][j] = ' '.join(keys['Keys'][i][j])
        #add leading and trailing whitespace
        keys['Keys'][i][j] = " " + keys['Keys'][i][j] + " "


######################################

####### read in pdf
##go into folder of 1 policy and read in all docs
path = os.getcwd()+str("\\pdf_re\\DEVCO_countries\\")
# path = os.getcwd()+str("\\pdf_re\\pdf\\")
folders = [folder for folder in listdir(path)]


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
typeerror_ls = []
valueerror_ls = []
syntaxerror_ls = []
counter = 0
for item in folders:
    print(item)
    counter = counter + 1
    temp_path = path + str(item)
    files = [file for file in listdir(temp_path) if isfile(join(temp_path, file))]
    if len(files) > 0:
        try:
            policy_texts = []
            for pdf_item in files:
                #scrape text from pdf
                file_path = temp_path + "\\" + str(pdf_item)
                pdfConverter = PdfConverter(file_path=file_path)
                try:
                    policy_texts.append(pdfConverter.convert_pdf_to_txt())
                except ValueError:
                    valueerror_ls.append(tuple((item, pdf_item)))
                    pass
                except SyntaxError:
                    syntaxerror_ls.append(tuple((item, pdf_item)))
                    pass
                except TypeError:
                    typeerror_ls.append(tuple((item, pdf_item)))
                    pass
            PDFtext.append([item, ' ; '.join(policy_texts)])
        except ValueError:
            valueerror_ls.append(tuple((item, pdf_item)))
            print("Value Error for: ", item)
            pass
        except TypeError:
            typeerror_ls.append(tuple((item, pdf_item)))
            pass

print(PDFtext)
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
    item[1] = [re.sub(r"/[^a-zA-Z0-9 ]/g", '', t.lower().strip()) for t in item[1]]
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
    print(item[1])
    # stem words
    item[1] = [stem(word) for word in item[1] if not word in stop_words]
    #remove special char for detection in text
    #try lemmatizing
    # item[1] = [lemmatizer.lemmatize(word) for word in item[1] if not word in stop_words]
    # merge back together to 1 string
    item[1] = ' '.join(item[1])
    #add trailing leading whitespace
    item[1] = " " + item[1] + " "
    item = item.append(len(item[1]))


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
            final_ls.append([item[0], keys['Goal'][i], keys['Keys'][i][j], counter, len(item[1])])

final_df = pd.DataFrame(final_ls, columns=['Policy', 'Goal', 'Keyword', "Count", "Textlength"])

#drop rows where keyword = ""
# print(len(final_df['Target']))
final_df = final_df[final_df.Keyword != ""]
# print(len(final_df['Target']))

#drop rows where count = 0
# print(len(final_df['Target']))
final_df = final_df[final_df.Count != 0]
# print(len(final_df['Target']))

# Create a Pandas Excel writer using XlsxWriter as the engine.
writer = pd.ExcelWriter(os.getcwd()+str("\\results\\raw\\mapping_goal_level_TEI_DEVCO_16112020.xlsx"), engine='xlsxwriter')

#export final output
final_df.to_excel(writer, sheet_name='RAW')
writer.save()

#############################
