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
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


#######################
##############################
#############################################
##########################################################
######################################################################

###################################################################################################
#################### FIRST BLOCK - COUNT SDG TARGETS IN DOCUMENTS #################################
###################################################################################################

######################################################################
##########################################################
##############################################
###############################
########################


#get date for file exports
date = time.strftime("%d%m%Y")

# set stop words
stop_words = set(stopwords.words("english"))


#create GUI for file dialogues
root = tk.Tk()
root.withdraw()



#################################################################
####### read in pdf
##function to get list with policies and their directory paths
def read_documents():
    messagebox.showinfo("Information", "Please select directory with Documents to be scanned")
    pdf_path = filedialog.askdirectory()
    folders = [folder for folder in listdir(pdf_path)]
    return folders, pdf_path
##################################################################

##################################################################
#function to export the folder list
def export_folderlist(folder_list):
    print(len(folder_list), " Policies found")
    workbook = xlsxwriter.Workbook(str('list_of_policies_') + str(date) + str('.xlsx'))
    worksheet = workbook.add_worksheet()
    row = 0
    column = 0
    for item in folders:
        # write operation perform
        worksheet.write(row, column, item)
        # incrementing the value of row by one
        # with each iteratons.
        row += 1
    workbook.close()
    return print("Folder List has been exported as Excel")
#######################################################################


######################################################################
########## CREATE CLASS FOR SCRAPING TEXT FROM PDFs ##################
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
#######################################################



######################################################
#function to scrape text from documents and save policy names where the text scrape did not work
# input must be the folder list and the path to the PDFs
def get_text_data(folder_list, path):
    PDFtext = []
    typeerror_ls = []
    valueerror_ls = []
    syntaxerror_ls = []
    counter = 0
    for item in folder_list:
        print(item)
        temp_path = path + str("\\") + str(item)
        files = [file for file in listdir(temp_path) if isfile(join(temp_path, file))]
        count_docs = 0
        if len(files) > 0:
            count_docs = len(files)
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
            counter = counter + count_docs
    print(PDFtext)
    print("Number of docs: ", len(PDFtext))
    print("Number of folders: ", counter)
    return PDFtext, valueerror_ls, syntaxerror_ls, typeerror_ls
##############################################################################



##########################################################################
#function to count keywords
def count_keywords(text_data, keys):
    final_ls = []
    ##make the count
    for item in text_data:
        for key in keys:
            # print(keys['Keys'][i][j])
            counter = item[1].count(str(key))
            #write counter together with target, policy, keyword as new row in df
            #first write output to list
            final_ls.append([item[0], 'SDG', key, counter, len(item[1])])
    final_df = pd.DataFrame(final_ls, columns=['Policy', 'Target', 'Keyword', "Count", "Textlength"])
    # drop rows where keyword = ""
    final_df = final_df[final_df.Keyword != ""]
    # drop rows where count = 0
    final_df = final_df[final_df.Count != 0]
    return final_df
#########################################################################




##########################################################################################
#function to export final output to Excel, input needs to be Pandas DF
def export_df_to_Excel(df1):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(str(os.getcwd() + str("\\results\\raw\\mapping_") + str(date) + str(".xlsx")), engine='xlsxwriter')
    # export final output
    df1.to_excel(writer, sheet_name='RAW')
    #export final output
    writer.save()
    return print(str("Data has been successfully exported to Excel as ") + str("mapping_") + str(date) + str(".xlsx"))
###########################################################################################


###########################################################################################
######## call functions
#read in the keywords for each SDG target
keywords = ['sustainable', 'sustainability']


#read in the file directory for the documents and get the list of folders and the directory path
folders, pdf_path = read_documents()



#####uncomment to export folderlist
#export_folderlist(folders)

#scrape text from PDFs, get lists of error messages from scraping process
PDF_text, value_errors, syntax_errors, type_errors = get_text_data(folders, pdf_path)

final_df = count_keywords(PDF_text, keywords)

#export everything to final excel table
export_df_to_Excel(final_df)
#################################################################################


