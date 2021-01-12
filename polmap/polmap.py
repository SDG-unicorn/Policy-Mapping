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

def prepare_keywords(keywrds_string, stop_words, exception_dict=None):
    """
    Prepare keywords for mapping.
    """
    
    # if keywrds_string is not str:
    #     raise TypeError('keywrds_string is not a string') 
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
   
    keywrds_string = keywrds_string.split(";")
    keywrds_list = map(lambda term: term.split(),  keywrds_string)
    
    keywrds_list = [ [term.lower().strip() for term in terms]
                      for terms in keywrds_list ]
    keywrds_list = [ [re.sub(r"[^a-zA-Z-]+", '', term) for term in terms]
                      for terms in keywrds_list ]
    keywrds_list = [ [term.center(len(term)+2) for term in terms]
                      for terms in keywrds_list ]
    keywrds_list = [ [term.replace(" rd ", "R&D") for term in terms]
                      for terms in keywrds_list ]
    keywrds_list = [ [term for term in terms if len(term) > 2 or term == "ph" ]
                      for terms in keywrds_list ] 
    # not sure this is working the way intended, 
    # if the plan was to drop two characters words,
    # it is not  as we are however counting also spaces.
    # an easy fix would be to move it before the centering of the terms
    keywrds_list = [ [term.strip(' ') for term in terms]
                      for terms in keywrds_list ]
    
    keywrds_list = [ [exception_dict[term] if term in exception_dict.keys() 
                      else term
                      for term in terms]
                      for terms in keywrds_list ]
    
    keywrds_list = [ [ stem(term) for term in terms 
                      if not term in stop_words if term != "aids" ]
                      for terms in keywrds_list ]
    
    keywrds_list = [ [reverse_exception_dict[term] if term in reverse_exception_dict.keys() 
                      else term
                      for term in terms]
                      for terms in keywrds_list ]  
        
    keywrds_list = [ ' '.join(terms) for terms in keywrds_list ]
    keywrds_list = [ ' '+terms+' ' for terms in keywrds_list ]
    keywrds_list = [terms for terms in keywrds_list if terms!='  ']
    
    return keywrds_list