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

from whoosh.lang.porter import stem
import re
import nltk as nltk
from docx2python import docx2python
import pdfminer.high_level as pdfhl
from bs4 import BeautifulSoup

def preprocess_text(text_string, stop_words, exception_dict=None):
    """
    Prepare text for mapping.
    """
    
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
        raise TypeError('exception_dict is not a dict')
    
    reverse_exception_dict={value : key for key, value in exception_dict.items()}
    
    #remove all from stop_words to keep in keywords.
    # Review scoping rules in python, this fails with:
    # NameError: name 'stop_words' is not defined when called in lambda function
    # I would expect the variable to always exist whenever calling the function, but it does not.
    #if stop_words==None:
    #    stop_words = set(nltk.corpus.stopwords.words("english"))
    #    stop_words.remove("all")
   
    text_string = text_string.split(";")
    text_list = map(lambda term: term.split(),  text_string)
    
    text_list = [ [term.lower().strip() for term in terms]
                      for terms in text_list ]
    text_list = [ [re.sub(r"[^a-zA-Z-]+", '', term) for term in terms]
                      for terms in text_list ]
    text_list = [ [term.center(len(term)+2) for term in terms]
                      for terms in text_list ]
    text_list = [ [term.replace(" rd ", "R&D") for term in terms]
                      for terms in text_list ]
    text_list = [ [term for term in terms if len(term) > 2 or term == "ph" ]
                      for terms in text_list ] 
    # not sure this is working the way intended, 
    # if the plan was to drop two characters words,
    # it is not  as we are however counting also spaces.
    # an easy fix would be to move it before the centering of the terms
    text_list = [ [term.strip(' ') for term in terms]
                      for terms in text_list ]
    
    text_list = [ [exception_dict[term] if term in exception_dict.keys() 
                      else term
                      for term in terms]
                      for terms in text_list ]
    
    text_list = [ [ stem(term) for term in terms 
                      if not term in stop_words if term != "aids" ]
                      for terms in text_list ]
    
    text_list = [ [reverse_exception_dict[term] if term in reverse_exception_dict.keys() 
                      else term
                      for term in terms]
                      for terms in text_list ]  
        
    text_list = [ ' '.join(terms) for terms in text_list ]
    text_list = [ ' '+terms+' ' for terms in text_list ]
    text_list = [terms for terms in text_list if terms!='  ']
    
    return text_list



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

  