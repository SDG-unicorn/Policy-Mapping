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


##############################################
###write function to read in keyword list
def read_keywords():
    messagebox.showinfo("Information","Please select the file containing the list of keywords")
    keyword_path = filedialog.askopenfilename()
    keys = pd.read_excel(keyword_path, sheet_name= 'Sheet1' )
    ##read in 1 row with keys per target
    ## split row by ; - series of list of strings
    keys['Keys'] = keys['Keys'].str.split(pat = ";")
    return keys
###############################################


##############################################
#function for processing keywords
def process_keywords(keys):
    ##process words - remove stopwords, stemming, lemmatizing
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
            keys['Keys'][i][j] = [w.replace("remittance", "remit&tance&") for w in keys['Keys'][i][j]]
            keys['Keys'][i][j] = [w.replace("sme", "s&m&e") for w in keys['Keys'][i][j]]
            keys['Keys'][i][j] = [w.replace("smes", "s&m&e") for w in keys['Keys'][i][j]]
            #stem words
            keys['Keys'][i][j] = [stem(word) for word in keys['Keys'][i][j] if not word in stop_words if word != "aids"]
            # remove special char for detection in text
            keys['Keys'][i][j] = [w.replace("ai&ds&", "aids") for w in keys['Keys'][i][j]]
            keys['Keys'][i][j] = [w.replace("pro&ductivity&", "productivity") for w in keys['Keys'][i][j]]
            keys['Keys'][i][j] = [w.replace("remit&tance&", "remittance") for w in keys['Keys'][i][j]]
            keys['Keys'][i][j] = [w.replace("s&m&e", "SMEs") for w in keys['Keys'][i][j]]
            # lemmatizing words
            # keys['Keys'][i][j] = [lemmatizer.lemmatize(word) for word in keys['Keys'][i][j] if not word in stop_words]
            #merge back together to 1 string
            keys['Keys'][i][j] = [w for w in keys['Keys'][i][j] if len(w) > 0]
            keys['Keys'][i][j] = ' '.join(keys['Keys'][i][j])
            #add leading and trailing whitespace
            keys['Keys'][i][j] = " " + keys['Keys'][i][j] + " "
    return keys
#################################################################


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
    for item in folder_list:
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
    print("Number of folders: ", len(PDFtext))
    print("Number of docs: ", counter)
    return PDFtext, valueerror_ls, syntaxerror_ls, typeerror_ls
##############################################################################


##############################################################################
#function to export error messages
def export_error_messages(typeerrors, valueerrors, syntaxerrors):
    with open(os.getcwd()+str("\\error_reports\\error_messages_") + str(date) + str(".txt"), 'w') as fp:
        fp.write(("Type Errors Recorded for: "))
        fp.write('\n')
        fp.write('\n'.join('%s %s' % x for x in typeerrors))
        fp.write('\n')
        fp.write(("Value Errors Recorded for: "))
        fp.write('\n')
        fp.write('\n'.join('%s %s' % x for x in valueerrors))
        fp.write('\n')
        fp.write(("Syntax Errors Recorded for: "))
        fp.write('\n')
        fp.write('\n'.join('%s %s' % x for x in syntaxerrors))
    return print(str("Policies where Text Scrape failed were written to error_messages_") + str(date) + str(".txt"))
#########################################################################


#########################################################################
#function to process texts, input scraped PDF text
def process_texts(text):
    # init lemmatizer
    lemmatizer = WordNetLemmatizer()
    for item in text:
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
        item[1] = [w.replace("sme", "s&m&") for w in item[1]]
        item[1] = [w.replace("smes", "s&m&") for w in item[1]]
        print(item[1])
        # stem words
        item[1] = [stem(word) for word in item[1] if not word in stop_words]
        #remove special char for detection in text
        item[1] = [w.replace("ai&ds&", "aids") for w in item[1]]
        item[1] = [w.replace("pro&ductivity&", "productivity") for w in item[1]]
        item[1] = [w.replace("remit&tance&", "remittance") for w in item[1]]
        item[1] = [w.replace("s&m&", "SMEs") for w in item[1]]
        #try lemmatizing
        # item[1] = [lemmatizer.lemmatize(word) for word in item[1] if not word in stop_words]
        # merge back together to 1 string
        item[1] = ' '.join(item[1])
        #add trailing leading whitespace
        item[1] = " " + item[1] + " "
        item = item.append(len(item[1]))
    return text
#########################################################################


#########################################################################
##make list pandas df and export to check intermediately
#function to export text data
def export_textdata(text_data):
    # Create the pandas DataFrame
    df = pd.DataFrame(text_data, columns = ['Policy', 'Text', 'Textlength'])
    #no point in exporting since excel cuts off text after char len >32767
    #change directory respectively
    df.to_excel(str(os.getcwd()+str("\\results\\raw\\policy_mapping_textdat_") + str(date) + str(".xlsx")), sheet_name="RAW")
    return print(str("textdata has been exported to policy_mapping_textdata_") + str(date) + str(".xlsx"))
##########################################################################


##########################################################################
#function to count keywords
def count_keywords(text_data, keys):
    final_ls = []
    ##make the count
    for item in text_data:
        for i in range(0, len(keys['Keys'])):
            for j in range(0,len(keys['Keys'][i])):
                # print(keys['Keys'][i][j])
                counter = item[1].count(str(keys['Keys'][i][j]))
                #write counter together with target, policy, keyword as new row in df
                #first write output to list
                final_ls.append([item[0], keys['Target'][i], keys['Keys'][i][j], counter, len(item[1])])
    final_df = pd.DataFrame(final_ls, columns=['Policy', 'Target', 'Keyword', "Count", "Textlength"])
    # drop rows where keyword = ""
    final_df = final_df[final_df.Keyword != ""]
    # drop rows where count = 0
    final_df = final_df[final_df.Count != 0]
    final_df = final_df[final_df.Keyword != "  "]
    return final_df
#########################################################################


#########################################################################
##function to read in county names and process them
def get_developing_countries():
    messagebox.showinfo("Information","Please select the file containing the list of developing countries")
    keyword_path = filedialog.askopenfilename()
    countries_in = pd.read_excel(keyword_path, sheet_name= 'developing_countries')
    countries = countries_in['Name'].values.tolist()
    country_ls = []
    for element in countries:
        element = [re.sub(r"[^a-zA-Z-]+", '', t.lower().strip()) for t in element.split()]
        element = [stem(word) for word in element if not word in stop_words]
        element = ' '.join(element)
        country_ls.append(element)
    return country_ls
#########################################################################


##########################################################################
##specific subset of relevant targets
def get_keywords_for_developing_countries():
    messagebox.showinfo("Information","Please select the file containing the list of keywords for developing countries")
    keyword_path = filedialog.askopenfilename()
    dev_count_keys = pd.read_excel(keyword_path, sheet_name= 'Sheet2' )
    #split keys
    dev_count_keys['Keys'] = dev_count_keys['Keys'].str.split(pat = ";")
    return dev_count_keys
###########################################################################


###########################################################################
#process keywords for developing countries
def process_keywords_for_developing_countries(dev_count_keys):
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
            dev_count_keys['Keys'][i][j] = [w for w in dev_count_keys['Keys'][i][j] if len(w) > 0]
    return dev_count_keys
#####################################################################################


#####################################################################################
def count_keys_developing_countries(PDFtext, dev_count_keys, country_ls):
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
    final_df = final_df[final_df.Keyword != ""]
    #drop rows where count = 0
    final_df = final_df[final_df.Count != 0]
    return final_df
##########################################################################################


##########################################################################################
#function to export final output to Excel, input needs to be Pandas DF
def export_df_to_Excel(df1, df2):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(str(os.getcwd() + str("\\results\\raw\\mapping_") + str(date) + str(".xlsx")), engine='xlsxwriter')
    # export final output
    df1.to_excel(writer, sheet_name='RAW')
    #export final output
    df2.to_excel(writer, sheet_name='RAW_dev_countries')
    writer.save()
    return print(str("Data has been successfully exported to Excel as ") + str("mapping_") + str(date) + str(".xlsx"))
###########################################################################################


###########################################################################################
def export_folder_list_and_doc_duplicates(folder_path):
    date = time.strftime("%d%m%Y")
    # create list with all folders
    folders = [folder for folder in listdir(folder_path)]
    # empty list where tuples will be appended
    df_ls = []
    empty_folders = []
    for item in folders:
        # name of the folder
        print(item)
        # path to the folder
        temp_path = folder_path + str(item)
        # get all files inside a folder as a list
        files = [file for file in listdir(temp_path) if isfile(join(temp_path, file))]
        # check if folders are emptym
        if len(files) > 0:
            # go through file list and create tuple for each file + respective folder name
            for pdf_item in files:
                temp_tuple = (pdf_item, item)
                # appen tuple to list
                df_ls.append(temp_tuple)
        else:
            empty_folders.append(item)
    f = open(str('empty_folders') + str(date) + str('.txt'), 'w')
    for ele in empty_folders:
        f.write(ele + '\n')
    f.close()
    # make final dataframe from tuple list
    df = pd.DataFrame(df_ls, columns=['Document_File', 'Foldername'])
    # group by files and concatenate folder names to see in which folders same files have been used
    df = df.groupby('Document_File')['Foldername'].apply(';'.join).to_frame().reset_index()
    # add new column to count in how many folders the document is used
    df["Count"] = ""
    # loop over df and count
    for index, row in df.iterrows():
        row["Count"] = row['Foldername'].count(';') + 1
    # sort descending
    df = df.sort_values(by='Count', ascending=False)
    # reset index for export
    df = df.reset_index(drop=True)
    folders_df = pd.DataFrame(folders)
    # write to excel
    filename = str("folder_list") + str(date) + str(".xlsx")
    writer = pd.ExcelWriter(os.getcwd() + str("\\results\\raw\\") + filename,
                            engine='xlsxwriter')
    # export final output
    folders_df.to_excel(writer, sheet_name='folder_list')
    df.to_excel(writer, sheet_name='multipurpose_docs')
    writer.save()
    return (print(str("Folder List exported successfully as") + filename))

###########################################################################################
######## call functions
#read in the keywords for each SDG target
keywords = read_keywords()

#process each keyword
processed_keywords = process_keywords(keywords)

#read in the file directory for the documents and get the list of folders and the directory path
folders, pdf_path = read_documents()

#####uncomment to export folderlist
#export_folderlist(folders)

#scrape text from PDFs, get lists of error messages from scraping process
PDF_text, value_errors, syntax_errors, type_errors = get_text_data(folders, pdf_path)

#export error messages to text file
export_error_messages(type_errors, value_errors, syntax_errors)

#process scraped text from PDFs
PDF_text = process_texts(PDF_text)

####### uncomment to export textdata scraped from PDFs
#export_textdata(PDF_text)

###make the final count of keywords in the text
final_df = count_keywords(PDF_text, processed_keywords)

##read in list of developing countries, synonyms
developing_countries = get_developing_countries()

#read in keywords for developing countries
keywords_developing_countries = get_keywords_for_developing_countries()

#process keywords for developing countries
keywords_developing_countries = process_keywords_for_developing_countries(keywords_developing_countries)

#count keywords for developing countries
developing_countries_df = count_keys_developing_countries(PDF_text, keywords_developing_countries, developing_countries)

#export everything to final excel table
export_df_to_Excel(final_df, developing_countries_df)

#export list of policies and list of duplicate documents
#harmonise path, make it being returned by functions above
path = os.getcwd()+str("\\pdf_re\\Final_Run\\")
export_folder_list_and_doc_duplicates(path)

#################################################################################


##################################################################################
########################################################################
###############################################################
######################################################
#############################################
#####################################


###############################################################
########### SECOND BLOCK - PROCESS RESULTS ####################
###############################################################


######################################
##############################################
######################################################
##############################################################
####################################################################
#################################################################################

#append first and second df to have all results in one df
results = final_df.append(developing_countries_df, ignore_index=True)

##############################################################
#get list of undetected policies
def get_undetected_policies(df, folder_list):
    detected_pol = df['Policy'].tolist()
    detected_pol = list(dict.fromkeys(detected_pol))
    #make list with policies not detected
    undetected_pol = [x for x in folder_list if x not in detected_pol]
    print(str(len(undetected_pol)) + str(" Policies where no targets were detected"))
    return undetected_pol

#call function
undetected_pol = get_undetected_policies(results, folders)
with open(str() + str('undetected_policies') + str(date) + str('.txt'), 'w') as filehandle:
    filehandle.writelines("%s\n" % policy for policy in undetected_pol)

##############################################################


##############################################################
##count keywords per policy per target

