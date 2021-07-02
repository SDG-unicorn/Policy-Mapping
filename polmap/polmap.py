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
#Built-in
import re, collections, pathlib, math

#doc2txt
from docx2python import docx2python
import pdfminer.high_level as pdfhl
from bs4 import BeautifulSoup
#check https://textract.readthedocs.io/en/stable/

#preprocess_text
import whoosh.lang as whla
import nltk as nltk
from nltk.corpus import stopwords
#get_ref_to_SDGs


####### Create output directory tree.

def make_dirtree(output_directory):
    """
    Define a dictionary representing output directory tree.
    """

    output_directory = pathlib.Path(output_directory) / 'output'

    directory_dict = {
        'out_dir' : output_directory ,
        'log_dir' : output_directory / '0-logs' ,
        'processed_keywords_dir' : output_directory / '1-processed_keywords' ,
        'doctext_dir' : output_directory / '2-doctext' ,
        'references_dir' : output_directory / '3-references',
        'doctext_stemmed_dir' : output_directory / '4-doctext_stemmed' ,        
        'keyword_count_dir' : output_directory / '5-keyword_count',
        'results_dir' : output_directory / '6-results',
        'jsonfiles_dir' : output_directory / '7-json_results'
    }

    return directory_dict


###### Extract text from doc and docx files.

def doc2text(a_document_path):
    """
    Helper function that calls different document to text converting functions 
    based on the document filetype.

    Expected input is a path to a document, ideally as pathlib.
    """

    suffix = a_document_path.suffix

    plain_text = ['.txt','.rtf']

    ms_word = ['.doc','.docx']

    html = ['.html', '.mhtml']

    d2t_dict = {'.doc' : docx2python,
                '.docx' : docx2python,
                '.pdf' : pdfhl.extract_text,
                '.html' : BeautifulSoup,
                '.mhtml' : BeautifulSoup                
    }

    if suffix in plain_text:
        with open(a_document_path,'r') as file_:
            text_from_doc = file_.read()
    elif suffix in ms_word:
        text_from_doc = d2t_dict[suffix](a_document_path).text
    elif suffix in html:
        with open(a_document_path, 'r') as file_:
            text_from_doc = d2t_dict[suffix](file_, "html.parser").get_text()
    else:
        text_from_doc = d2t_dict[suffix](a_document_path)
    
    return text_from_doc


####### Preprocess and stem text.

stop_words = set(stopwords.words('english'))-set(['no','not','nor']) 

def preprocess_text(a_string, stop_words, exception_dict=None, regex_dict=None):
    """
    Prepare text for mapping.
    """
    text_string = str(a_string)

    if text_string is None: #this should be moved to the prepare keywords wrapper function
        return None
    # if text_string is not str:
    #     raise TypeError('text_string is not a string') 
    #     #How to return the name of the variable passed by user with format?
    # Get error when using it with apply and lambda in pandas
    
    if exception_dict is None:
        exception_dict = {"aids": "ai&ds&",
                          "productivity": "pro&ductivity&",
                          "remittances" : "remit&tance&"                 
                          }
    elif exception_dict is not dict:
        raise TypeError(f'{exception_dict} is not of type dict')
    

    if regex_dict is None:
        regex_dict = collections.OrderedDict([(r'[^a-zA-Z0-9.,;:\s-]+', ''), 
        (r'([\w-]+)', r' \1 '),
        (r'(\w)([.,;:])', r'\1 \2'),
        (r'([\w ])\n([\w ])', r'\1 \2')])
    elif not isinstance(regex_dict, collections.OrderedDict): #Requires Python => 3.7, otherwise needs OrderedDict object
        raise TypeError(f'{regex_dict} is not of type Ordered dict')       


    #Instantiate stemmer
    stemmer = nltk.stem.PorterStemmer()

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
    
    text_string = re.sub(r'([a-zA-z-]{3,}|ph|no|eu)', r'\1', text_string) #add |no for detecting 'no poverty' keyword
    
    # not sure this is working the way intended, 
    # if the plan was to drop two characters words,
    # it is not  as we are however counting also spaces.
    # an easy fix would be to move it before the centering of the terms
    
    for key, value in exception_dict.items(): #Protect exceptions from stemming
        text_string = text_string.replace(key, value)
    
    for word in stop_words: #Remove stopwords
        text_string = text_string.replace(' '+word+' ', '') 
    
    text_string = re.sub(r'[a-zA-z&-]+', #Find words with regex. It can be improved by capturing pattern between word boundaries.
    lambda rgx_word: ' '+stemmer.stem(rgx_word.group())+' ', #Stem words, however stemming is skipped if string contains space.
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

    if refs_keywords is None:
        refs_keywords = ["SDG", "Sustainable Development Goals", "Sustainable Development principles", "Agenda 2030", "2030 Agenda", "UN Agenda for sustainable development"]
    
    elif not isinstance(refs_keywords, (collections.Iterable,collections.Container)):
        raise TypeError(f'{refs_keywords} is not an iterable and a container')
    
    elif len(refs_keywords)==0:
        raise ValueError(f'{refs_keywords} is empty')
    
    refs_keywords = [ref_keyword.lower() for ref_keyword in refs_keywords]

    #compare lists and get matches
    refs_sentences = {}
    for sentence in document_sentences:
        if any(ref_keyword in sentence for ref_keyword in refs_keywords):
            tagged_sentence = sentence
            for ref_keyword in refs_keywords:
                tagged_sentence=tagged_sentence.replace(ref_keyword, f'<span>{ref_keyword}</span>')
            refs_sentences[tagged_sentence.capitalize()] = ', '.join([f'<span>{ref_keyword.capitalize()}</span>' for ref_keyword in refs_keywords if ref_keyword in sentence])        
    
    return refs_sentences

def join_str(numpy_array):

    numpy_array = numpy_array.tolist()
    numpy_array = [ item for item in numpy_array if not isinstance(item, float) ]
    numpy_array = ', '.join(numpy_array)
    
    return numpy_array

# def mark_text(pd_row, doc_text, keywd_cols=list(range(57))):
#     #print(pd_row)
#     label = str(pd_row['Target'])
#     flag = label.split('.')[-1]
#     flag = 'SDG' if flag=='0' else 'Target'
#     for keywd in pd_row[keywd_cols]:
#         #print(keywd, type(keywd))
#         if not isinstance(keywd, float):
#             doc_text=doc_text.replace(keywd, f'< {flag} {label} <{keywd.upper()}>>')
#         else:
#             continue
#         if flag=='SDG':
#             doc_text=doc_text.replace('.0','') 
#     return doc_text

def mark_text(document_text, detected_keywords_df):

    marked_text = document_text 

    for _, row in detected_keywords_df.iterrows():

        label = row['Target'] if row['Target'].split('.')[-1] != '0' else row['Goal']
        
        for keyword in row[range(57)]:
            #print(keyword)
            if keyword and not isinstance(keyword, float):
                marked_text = marked_text.replace(keyword ,f' < {label} >< {keyword.upper()} > ')

    return marked_text