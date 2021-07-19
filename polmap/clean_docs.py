
# -*- coding: utf-8 -*-


"""
..
  .. see also:: 
  Developers involved:
  * Michele Maroni <github: michelemaroni>
  * Steve Borchardt <github: SDG-unicorn>
  Organizations involved:
  * `name <url>`_
  :license: 
  :requires: 
"""

import re, copy

def clean_jpb(jpb_text):#jpb_parameters='default'
  """
  Set of string manipulations for cleaning JRC project browser documents for SDG mapping
  """

  clean_text=jpb_text

  clean_dict={'Main Pol. DG':None,'Beneficiary DGs':None,\
      'Other interested DGs and stakeholders':None,'Customer DG':None,\
        'Legal basis':None, 'Horizon Europe - Areas of intervention':None}

  get_DGs='\n{1,3}([a-zA-z,()\/ -]{1,}|\n)\n'
  fields=clean_dict.keys()
  fields={key: get_DGs for key in fields}
  fields['Legal basis']=get_DGs
  fields['Horizon Europe - Areas of intervention']=''

  for field in fields.keys():
    pattern=rf'{field}'+fields[field]
    pattern=re.compile(pattern)
    #print(pattern)
    clean_dict[field]=re.findall(pattern, clean_text)
    #print(clean_dict[field])
    clean_text=re.sub(pattern, '' ,clean_text)

  #print('\n')

  return clean_text, clean_dict

    

