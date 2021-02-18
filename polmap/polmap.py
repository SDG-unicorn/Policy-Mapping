# -*- coding: utf-8 -*-

"""
..
  .. seealso:: 
  Developers involved:
  * Michele Maroni <github: michelemaroni>
  * Steve Borchardt <github: SDG-unicorn>
  Organizations involved:
  * `name <url>`_
  :license: 
  :requires: 
"""

#Imports

#make_directories
import datetime as dt
import pathlib
import warnings

#preprocess_text
from whoosh.lang.porter import stem
import re
import nltk as nltk
import collections

#doc2txt
from docx2python import docx2python
import pdfminer.high_level as pdfhl
from bs4 import BeautifulSoup


####### Create output directory tree.

def make_directories(input_directory, out_dir='current'):

    current_date = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

    project_title = input_directory.name+'_'+current_date

    if out_dir=='current':
        out_dir = pathlib.Path.cwd() / 'output' / project_title
    elif not isinstance(out_dir, pathlib.Path): #test if out dir is of type path
        raise TypeError('out_dir is not pathlib.Path object') #Try to convert out dir into path, test if exist, try to make it.

    directory_dict = {
        'out_dir' : out_dir ,
        'log_dir' : out_dir / 'logs' ,
        'results_dir' : out_dir / 'results' ,
        'doctext_dir' : out_dir / 'doctext' ,
        'doctext_stemmed_dir' : out_dir / 'doctext_stemmed' ,
        'processed_keywords_dir' : out_dir / 'processed_keywords' ,
        'keyword_count_dir' : out_dir / 'keyword_count'
    }

    
    for directory in directory_dict.values():
        directory.mkdir(mode=0o777, parents=True, exist_ok=True)

    return directory_dict


####### Preprocess and stem text.

def preprocess_text(a_string, stop_words, exception_dict=None, regex_dict=None):
    """
    Prepare text for mapping.
    """
    text_string = a_string

    if text_string==None: #this should be moved to the prepare keywords wrapper function
        return None
    # if text_string is not str:
    #     raise TypeError('text_string is not a string') 
    #     #How to return the name of the variable passed by user with format?
    # Get error when using it with apply and lambda in pandas
    
    if exception_dict==None:
        exception_dict = {"aids": "ai&ds&",
                          "productivity": "pro&ductivity&",
                          "remittances" : "remit&tance&"                 
                          }
    elif exception_dict is not dict:
        raise TypeError('exception_dict is not of type dict')
    

    if regex_dict == None:
        regex_dict = collections.OrderedDict([(r'[^a-zA-Z0-9. -]+', ''), (r'([\w-]+)', r' \1 ')])
    elif not isinstance(regex_dict, collections.OrderedDict):
        raise TypeError('regex_dict is not of type Ordered dict')
        

    #remove all from stop_words to keep in keywords.
    # Review scoping rules in python, this fails with:
    # NameError: name 'stop_words' is not defined when called in lambda function
    # I would expect the variable to always exist whenever calling the function, but it does not.
    #if stop_words==None:
    #    stop_words = set(nltk.corpus.stopwords.words("english"))
    #    stop_words.remove("all")

       
    #text_string = text_string.replace('\xa0',' ') #Remove some weird \xa0 characters

    text_string = text_string.lower().strip()

    for pattern, substitution in regex_dict.items():
        text_string = re.sub(pattern, substitution, text_string)
    
    #text_string = re.sub(r'([\w-]+)', r' \1 ', text_string) #Equivalent to center, adds leading and trailing space to the captured group
    
    text_string = text_string.replace(' rd ', ' R&D ')
    
    text_string = re.sub(r'([a-zA-z-]{3,}|ph)', r'\1', text_string)
    
    # not sure this is working the way intended, 
    # if the plan was to drop two characters words,
    # it is not  as we are however counting also spaces.
    # an easy fix would be to move it before the centering of the terms
    
    for key, value in exception_dict.items(): #Protect exceptions from stemming
        text_string = text_string.replace(key, value)
    
    for word in stop_words: #Remove stopwords
        text_string = text_string.replace(' '+word+' ', '') 
    
    text_string = re.sub(r'[a-zA-z&-]+', #Find words wirth regex. It can be improved by capturing pattern between word boundaries.
    lambda rgx_word: ' '+stem(rgx_word.group())+' ', #Stem words, however stemming is skipped if string contains space.
    text_string)
        
    for key, value in exception_dict.items(): #Restore words from exception protection
        text_string = text_string.replace(value, key)
    
    text_string = ' '+text_string+' '
    
    text_string = re.sub(r' {2,}', r' ', text_string)
        
    return text_string


###### Extract text from doc and docx files.

def doc2text(a_document_path):
    """
    Helper function that calls different document to text converting functions 
    based on the document filetype.

    Expected input is a path to a document, ideally as pathlib.
    """

    suffix = a_document_path.suffix

    ms_word = ['.doc','.docx']

    html = ['.html', '.mhtml']

    d2t_dict = {'.doc' : docx2python,
                '.docx' : docx2python,
                '.pdf' : pdfhl.extract_text,
                '.html' : BeautifulSoup,
                '.mhtml' : BeautifulSoup                
    }

    if suffix in ms_word:
        text_from_doc = d2t_dict[suffix](a_document_path).text
    elif suffix in html:
        with open(a_document_path, 'r') as file_:
            text_from_doc = d2t_dict[suffix](file_, "html.parser").get_text()
    else:
        text_from_doc = d2t_dict[suffix](a_document_path)
    
    return text_from_doc

  