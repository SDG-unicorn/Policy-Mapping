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

    keyword_columns = detected_keywords_df.drop(columns=['Goal', 'Target']).columns.tolist()

    for _, row in detected_keywords_df.iterrows():

        label = row['Target'] if row['Target'].split('.')[-1] != '0' else row['Goal']
        
        for keyword in row[keyword_columns]:
            #print(keyword)
            if keyword and not isinstance(keyword, float):
                marked_text = marked_text.replace(keyword ,f' < {label} >< {keyword.upper()} > ') #Use re.search to find keyword boundaries where to add the tags and markers

    return marked_text