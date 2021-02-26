import argparse

parser = argparse.ArgumentParser(description="""Keyword counting program.
Given a set of keywords, and a set of pdf, docx and html documents in a directory, it counts in each documents how many times a certain keyword is found.
The results are provided for both the whole run and for each documents, together with the raw and stemmed text of the documents and keywords.""")
parser.add_argument('-i', '--input', help='Input directory')
parser.add_argument('-o', '--output', help='Output directory')
parser.add_argument('-k', '--keywords', help='Keywords file')

args = parser.parse_args()

print(args)