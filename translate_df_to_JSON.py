import json
import os
import pandas as pd



# read in mapping results
df_goal = pd.read_excel(os.getcwd()+str("\\results\\processed\\bubbleplot\\data_for_bubbleplot_VdL_17122020_processed.xlsx"), sheet_name="Policies_per_Goal")
df_target = pd.read_excel(os.getcwd()+str("\\results\\processed\\bubbleplot\\data_for_bubbleplot_VdL_17122020_processed.xlsx"), sheet_name="Policies_per_Target")
#remove Target string from Var1 cells
df_target['Var1'] = 'Target ' + df_target['Var1'].astype(str)


###########JSON for all policies###########################
#subset goal df
goal_subset = df_goal[['SDG', 'n_pol']]
goal_subset = goal_subset.rename(columns={'SDG':'name', 'n_pol':'size'}, inplace=False)

#subset only target, goal, freq
target_subset = df_target[['Var1', 'Freq', 'Goal']]
target_subset = target_subset.rename(columns={'Var1':'name', 'Freq':'size', 'Goal':'Goal'}, inplace=False)


#creating list of dicts for each SDG
gb = target_subset.groupby('Goal', sort=False)
ls = [gb.get_group(x) for x in gb.groups]
dict_ls = []
for i in range(0, len(ls)):
    label = ls[i]['Goal'].unique()
    print(label)
    #get size for SDG bubble
    size = goal_subset.iloc[i]['size']
    print(size)
    #create list of dicts for each SDG
    tmp_ls = []
    for row_dict in ls[i].to_dict(orient="records"):
        tmp_ls.append(row_dict)
    #make final dict with label, size, list of dicts and append to dict_list
    tmp_dict = {'name':label[0],'size':str(size),'children':tmp_ls}
    dict_ls.append(tmp_dict)


final_dict = {'name':"sdgs", 'children':dict_ls}

path = os.getcwd()+str("\\Diego")
filename = "VdL_17122020_policy-mapping-all.json"
complete_path = os.path.join(path, filename)
with open(complete_path, 'w') as fp:
    json.dump(final_dict, fp)


######################################################


###########jSON for legally binding only #######################

#subset goal df
goal_subset = df_goal[['SDG', 'cat_1']]
goal_subset = goal_subset.rename(columns={'SDG':'name', 'cat_1':'size'}, inplace=False)

#subset only target, goal, freq
target_subset = df_target[['Var1', 'cat_1', 'Goal']]
target_subset = target_subset.rename(columns={'Var1':'name', 'cat_1':'size', 'Goal':'Goal'}, inplace=False)


#creating list of dicts for each SDG
gb = target_subset.groupby('Goal', sort=False)
ls = [gb.get_group(x) for x in gb.groups]
dict_ls = []
for i in range(0, len(ls)):
    label = ls[i]['Goal'].unique()
    print(label)
    #get size for SDG bubble
    size = goal_subset.iloc[i]['size']
    print(size)
    #create list of dicts for each SDG
    tmp_ls = []
    for row_dict in ls[i].to_dict(orient="records"):
        tmp_ls.append(row_dict)
    #make final dict with label, size, list of dicts and append to dict_list
    tmp_dict = {'name':label[0],'size':str(size),'children':tmp_ls}
    dict_ls.append(tmp_dict)


final_dict = {'name':"sdgs", 'children':dict_ls}

path = os.getcwd()+str("\\Diego")
filename = "VdL_17122020_policy-mapping-legally-binding.json"
complete_path = os.path.join(path, filename)
with open(complete_path, 'w') as fp:
    json.dump(final_dict, fp)

##############################################################


##########JSON file for non-legally binding##################


#subset goal df
goal_subset = df_goal[['SDG', 'cat_2']]
goal_subset = goal_subset.rename(columns={'SDG':'name', 'cat_2':'size'}, inplace=False)

#subset only target, goal, freq
target_subset = df_target[['Var1', 'cat_2', 'Goal']]
target_subset = target_subset.rename(columns={'Var1':'name', 'cat_2':'size', 'Goal':'Goal'}, inplace=False)


#creating list of dicts for each SDG
gb = target_subset.groupby('Goal', sort=False)
ls = [gb.get_group(x) for x in gb.groups]
dict_ls = []
for i in range(0, len(ls)):
    label = ls[i]['Goal'].unique()
    print(label)
    #get size for SDG bubble
    size = goal_subset.iloc[i]['size']
    print(size)
    #create list of dicts for each SDG
    tmp_ls = []
    for row_dict in ls[i].to_dict(orient="records"):
        tmp_ls.append(row_dict)
    #make final dict with label, size, list of dicts and append to dict_list
    tmp_dict = {'name':label[0],'size':str(size),'children':tmp_ls}
    dict_ls.append(tmp_dict)


final_dict = {'name':"sdgs", 'children':dict_ls}

path = os.getcwd()+str("\\Diego")
filename = "VdL_17122020_policy-mapping-non-legally-binding.json"
complete_path = os.path.join(path, filename)
with open(complete_path, 'w') as fp:
    json.dump(final_dict, fp)
