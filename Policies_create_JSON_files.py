import json
import os
import pandas as pd


# read in mapping results
# map_dat = pd.read_excel('sankey_input_Old_Mapping_16122020.xlsx', sheet_name= 'RAW' )
#
#
# #create a dictionary with 2 keys: nodes and links and the values of each are list of dictionaries,
# # and nodes list  of dictionaries has to have keys: node, name, color
#
# #links list of dicts has to have keys: source, target, value , color
#
# #loop over df, take all entries for 1 policy, create nodes from policy name and targets, first index, then label, then respective SDGcolor
# #create unique list of Policy Names
# pol_ls = map_dat.Policy.unique()
# pol_ls = pol_ls.tolist()
# categories = pd.read_excel('policies_categories_final.xlsx', sheet_name='folder_list')
# categories = categories.loc[categories['Policy'].isin(pol_ls)]
# cat_ls = categories.Category.tolist()
#
# path = os.getcwd()+str("/json_files_old")
# for item in pol_ls:
#     print(pol_ls.index(item))
#     nodes_ls = []
#     links_ls = []
#     final_dict = {}
#     nodes_col = ['#3E3E3E']
#     nodes_id = [0]
#     links_source = []
#     links_target = []
#     links_val = []
#     links_col = []
#     temp_df = map_dat.loc[map_dat['Policy'] == item]
#     temp_df.reset_index(drop=True, inplace=True)
#     nodes_names = [temp_df.iloc[0]['Policy']]
#     nodes_description = [temp_df.iloc[0]['Target_Description']]
#     print(temp_df)
#     for ind in temp_df.index:
#         nodes_names.append(temp_df['Target'][ind])
#         nodes_col.append(temp_df['SDGcol'][ind])
#         nodes_id.append(int(ind + 1))
#         nodes_description.append(temp_df['Target_Description'][ind])
#         links_source.append(int(0))
#         links_target.append(int(ind + 1))
#         links_val.append(int(temp_df['aggr_Count'][ind]))
#         links_col.append(temp_df['SDGcol'][ind])
#     nodes_ls = [{'node': nodes_id[i], 'name': nodes_names[i], 'color': nodes_col[i], 'description': nodes_description[i]} for i in range(len(nodes_names))]
#     links_ls = [{'source': links_source[i], 'target': links_target[i], 'value': links_val[i], 'color': links_col[i]} for
#                 i in range(len(links_source))]
#     final_dict = {"nodes": nodes_ls, "links": links_ls, "Category": cat_ls[pol_ls.index(item)]}
#     filename = str(temp_df.iloc[0]['ID'] + 1) + '_' + temp_df.iloc[0]['Policy'] + '.json'
#     complete_path = os.path.join(path, filename)
#     with open(complete_path, 'w') as fp:
#         json.dump(final_dict, fp)


####for new mapping
# read in mapping results
map_dat = pd.read_excel('sankey_input_VdL_17122020.xlsx', sheet_name= 'RAW' )


#create a dictionary with 2 keys: nodes and links and the values of each are list of dictionaries,
# and nodes list  of dictionaries has to have keys: node, name, color

#links list of dicts has to have keys: source, target, value , color

#loop over df, take all entries for 1 policy, create nodes from policy name and targets, first index, then label, then respective SDGcolor
#create unique list of Policy Names
pol_ls = map_dat.celex.unique()
pol_ls = pol_ls.tolist()
categories = pd.read_excel(os.getcwd()+str("\\Query\\titles_codes_categories.xlsx"), sheet_name='folder_list')
categories = categories.loc[categories['celex_code'].isin(pol_ls)]

cat_ls = categories.category.tolist()
pol_ls = categories.celex_code.tolist()
title_ls = categories.title.tolist()



path = os.getcwd()+str("/json_files_new")
for item in pol_ls:
    print(pol_ls.index(item))
    nodes_ls = []
    links_ls = []
    final_dict = {}
    nodes_col = ['#3E3E3E']
    nodes_id = [0]
    links_source = []
    links_target = []
    links_val = []
    links_col = []
    temp_df = map_dat.loc[map_dat['celex'] == item]
    temp_df.reset_index(drop=True, inplace=True)
    nodes_names = [temp_df.iloc[0]['celex']]
    title = [temp_df.iloc[0]['Policy']]
    nodes_description = [temp_df.iloc[0]['Target_Description']]
    print(temp_df)
    for ind in temp_df.index:
        nodes_names.append(temp_df['Target'][ind])
        nodes_col.append(temp_df['SDGcol'][ind])
        nodes_id.append(int(ind + 1))
        nodes_description.append(temp_df['Target_Description'][ind])
        links_source.append(int(0))
        links_target.append(int(ind + 1))
        links_val.append(int(temp_df['aggr_Count'][ind]))
        links_col.append(temp_df['SDGcol'][ind])
    nodes_ls = [
        {'node': nodes_id[i], 'name': nodes_names[i],'title':title[0], 'color': nodes_col[i], 'description': nodes_description[i]} for i
        in range(len(nodes_names))]
    links_ls = [{'source': links_source[i], 'target': links_target[i], 'value': links_val[i], 'color': links_col[i]} for
                i in range(len(links_source))]
    final_dict = {"nodes": nodes_ls, "links": links_ls, "Category": cat_ls[pol_ls.index(item)]}
    filename = str(temp_df.iloc[0]['ID'] + 1) + '_' + temp_df.iloc[0]['celex'] + '.json'
    complete_path = os.path.join(path, filename)
    with open(complete_path, 'w') as fp:
        json.dump(final_dict, fp)
