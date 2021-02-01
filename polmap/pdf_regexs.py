#Series of regex to handle and clean text from pdfs converted with pdfminersix
#detect soft hyphen that separates words
doc_string = re.sub(r' {3,}', '\t', doc_string) #Replace triple spaces with tabs (useful for footnotes)
doc_string = re.sub(r' {2}', ' ', doc_string) #Remove double spaces (Frequent in text body)
#item[1] = re.sub(r'\t{2,} \n', r'', item[1]) #Remove a repetition of tabs ending with a space and a line return
doc_string = re.sub(r'([\w,:?!())]+) \n([\w()]+)', r'\1 \2', doc_string) #Remove line returns between words and commas
doc_string = re.sub(r'(\w+)([.,:;?!]\W+)', r'\1 \2', doc_string) #Add a space between words and punctation
#item[1] = re.sub(r'(\w+)\. \n?', r'\1.\n', item[1]) #Add line returns after each point    
doc_string = re.sub(r'-\n', '-', doc_string) #
doc_string = re.sub(r'(\d+ \n\n \n)', r'Page \1', doc_string) #Find page breaks and add a leading 'Page' string.
doc_string = re.sub(r' \n\n \n', r'', doc_string) #Remove the sequence of FF, space and line returns at the end of each page.
doc_string = re.sub(r'(\d+\t[A-Z]\w*)', r'Ref:\1', doc_string) # Find footnotes and add a leadin 'Ref:' string.
