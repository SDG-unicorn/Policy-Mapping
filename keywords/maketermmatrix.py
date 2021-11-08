import pathlib, argparse
import pandas as pd
import numpy as np
from natsort import index_natsorted

targets, goals = pd.ExcelFile('./keywords.xlsx').parse('Target_keys', usecols='A:B'), \
pd.ExcelFile('./keywords.xlsx').parse('Goal_keys',usecols='A:B')

targets['Goal'] = targets['Target'].apply(lambda label: f"SDG {label.split('.')[0]}")
goals['Target'] = goals['Goal'].apply(lambda label: f"{label.replace('SDG ', '')}.0")

term_matrix = pd.concat([targets,goals]).reindex(columns=['Goal','Target', 'Keys'])
term_matrix = term_matrix.sort_values(by="Target", key=lambda x: np.argsort(index_natsorted(term_matrix["Target"])))
term_matrix = term_matrix.reset_index()
matrix = term_matrix['Keys'].str.split(';' , expand=True)
matrix.fillna("", inplace=True)

term_matrix = pd.concat([term_matrix, matrix], axis='columns').drop(columns=['index', 'Keys'])
term_matrix.to_excel('term_matrix.xlsx',sheet_name='Term_matrix', index_label='Index')
