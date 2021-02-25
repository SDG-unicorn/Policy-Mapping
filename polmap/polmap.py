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
from typing import Container
import warnings

#doc2txt
from docx2python import docx2python
import pdfminer.high_level as pdfhl
from bs4 import BeautifulSoup

#preprocess_text
from whoosh.lang.porter import stem
import re
import nltk as nltk
import collections

#get_ref_to_SDGs


####### Create output directory tree.

def make_directories(input_directory, out_dir='current'):
    """
    Create an output directory tree.
    The parent output directory is named after the input directory and the datetime of execution.
    The output directory is created by default in the current working directory,
    unless and output path is passed in the out_dir optional argument.
    """


    current_date = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

    project_title = input_directory.name + '_' + current_date

    if out_dir=='current':
        out_dir = pathlib.Path.cwd() / 'output' / project_title
    elif not isinstance(out_dir, pathlib.Path): #test if out dir is of type path, should test also for its existence.
        raise TypeError(f'{out_dir} is not pathlib.Path object') #Try to convert out dir into path, test if exist, try to make it.

    directory_dict = {
        'out_dir' : out_dir ,
        'log_dir' : out_dir / 'logs' ,
        'results_dir' : out_dir / 'results' ,
        'processed_keywords_dir' : out_dir / '1-processed_keywords' ,
        'doctext_dir' : out_dir / '2-doctext' ,
        'references_dir' : out_dir / '3-references',
        'doctext_stemmed_dir' : out_dir / '4-doctext_stemmed' ,        
        'keyword_count_dir' : out_dir / '5-keyword_count'
    }

    
    for directory in directory_dict.values():
        directory.mkdir(mode=0o777, parents=True, exist_ok=True)

    return directory_dict


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
        raise TypeError(f'{exception_dict} is not of type dict')
    

    if regex_dict == None:
        regex_dict = collections.OrderedDict([(r'[^a-zA-Z0-9. -]+', ''), (r'([\w-]+)', r' \1 ')])
    elif not isinstance(regex_dict, collections.OrderedDict): #Requires Python => 3.7, otherwise needs OrderedDict object
        raise TypeError(f'{regex_dict} is not of type Ordered dict')       

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
    
    text_string = re.sub(r'([a-zA-z-]{3,}|ph)', r'\1', text_string) #add |no for detecting 'no poverty' keyword
    
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


##### Find and extract references to UN 2030 Agenda SDG  

def SDGrefs_mapper(document_text, refs_keywords=None):

    #tokenise string by sentence
    document_sentences = nltk.tokenize.sent_tokenize(document_text.lower())

    if refs_keywords == None:
        phrases = ["SDG", "Sustainable Development Goals", "Sustainable Development principles", "Agenda 2030", "2030 Agenda", "UN Agenda for sustainable development"]
    elif not isinstance(refs_keywords, (collections.Iterable,collections.Container)):
        raise TypeError(f'{refs_keywords} is not an iterable and a container')
    elif len(refs_keywords)==0:
        raise ValueError(f'{refs_keywords} is empty')
    
    refs_keywords = [ele.lower() for ele in phrases]

    #compare lists and get matches
    refs_sentences = {}
    for sentence in document_sentences:
        if any(keyword in sentence for keyword in refs_keywords):
            refs_sentences[sentence.capitalize()] = ', '.join([keyword.capitalize() for keyword in refs_keywords if keyword in sentence])        
    
    return refs_sentences