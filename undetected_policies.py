import io, csv, re, os, json
from os import listdir
from os.path import isfile, join
from nltk.corpus import stopwords
import pandas as pd
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

###########read in all keywords
path = os.getcwd()+str("\\Query\\VdL\\")
folders = [ folder for folder in listdir(path)]

detected_pol = pd.read_excel(os.getcwd()+str("\\results\\processed\\VdL_17112020.xlsx"), sheet_name='aggregated_to_target_level')

#policies for which no keys were detected
detected_pol = detected_pol['Policy'].tolist()

det_pol = []
for item in set(detected_pol):
    det_pol.append(item)

#make list with policies not detected
undet_pol = [x for x in folders if x not in det_pol]


#now try to scrape text from these PDFs again and write them to file.
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
for item in undet_pol:
    print(item)
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
                    pass
            PDFtext.append([item, ' ; '.join(policy_texts)])
        except ValueError:
            print("Value Error for: ", item)
            pass

pol_ls = []
txt_len = []
for item in PDFtext:
    pol_ls.append(item[0])
    txt_len.append(len(item[1]))

df = pd.DataFrame(list(zip(pol_ls, txt_len)),
               columns =['Policy', 'Textlength'])

print(len(df['Policy']))

df2 = df[df.Textlength != 0]

print(len(df2['Policy']))

df.to_excel("policies_with_NO_targets.xlsx", sheet_name="List")


# ##make list pandas df and export to check intermediately
# # Create the pandas DataFrame
