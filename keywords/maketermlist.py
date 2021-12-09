import pandas as pd

term_df=pd.read_excel('term_matrix.xlsx', index_col=0)
term_df.head()
sdgs = [f'SDG {n}' for n in range(1,18,1)]
print(sdgs)
# loop over sdg, select a sdg in temrs and filter, assingn it to a value, check if the valu corresdponds to sheet goal
# if it does concatenate it and stor it into dictionary, otherwise continue
keywords_dict = {}

for sdg in sdgs:
    keywords_df = pd.DataFrame(columns=['Goal','Target','Terms'])
    sdg_df = term_df[term_df.Goal == sdg]
    for row in sdg_df.itertuples():
        sheet=pd.DataFrame(data={'Terms':row}).iloc[3:]
        sheet = sheet.dropna()
        #sheet['Terms'] = sheet['Terms'].str.strip()
        sheet['Goal'] = row.Goal
        sheet['Target'] = row.Target
        sheet = sheet.reindex(columns=['Goal','Target','Terms'])
        keywords_df = pd.concat([keywords_df,sheet])
    keywords_dict[sdg]=keywords_df
  

pd.DataFrame().to_excel('keywords_for_translation.xlsx')

for key, value in keywords_dict.items():
    with pd.ExcelWriter('keywords_for_translation.xlsx', mode='a', engine='openpyxl') as destfile:
        value.to_excel(destfile, sheet_name=key)
