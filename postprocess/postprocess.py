import pathlib , argparse, json
import datetime as dt
import pandas as pd
import os
# from tkinter import filedialog
# from tkinter import *
# from nltk import tokenize

#######################################################
#######################################################
######  SET OPTIONS AND READ IN RELEVANT DATA  ########
#######################################################
#######################################################

# parser = argparse.ArgumentParser(description="""Aggregate mapping results.""")
# parser.add_argument('-i', '--input', help='Input file')
# parser.add_argument('-o', '--output', help='Output directory', default='cwd')
# parser.add_argument('-at', '--add_timestamp', help='Add a timestamp to output directory', type=bool, default=True)

# args = parser.parse_args()

# #get current time
# date = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

# #for testing/checking df outputs
# pd.set_option('display.max_rows', 500)
# pd.set_option('display.max_columns', 500)

# #print all columns
# # pd.set_option('display.max_columns', None)
# # pd.set_option('display.max_rows', None)

# input_dir=pathlib.Path(args.input)


#reference table with all goals, targets, id's, descriptions, hexcolorcodes
#sdg_reference_df = pd.read_excel("polmap/goal_target_list.xlsx", sheet_name="Sheet1") #MM not the correct way to import files in a module?

#######################################################
#######################################################
################  DEFINE FUNCTIONS  ##################
#######################################################
#######################################################

def stringify_id(pd_id_column, type=str):
    pd_id_column = pd_id_column.astype(type)
    return pd_id_column

#####################################
############################
####################
###############



######################
##############################
#####################################
#aggrgate to target level
#new column with number of keywords
# join all detected keywords in new column
def aggregate_to_targets(raw_df, sdg_references):
    #group rows by policy and by target and sum count
    dat_target_level = raw_df.groupby(['Policy', 'Target'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    dat_target_join_keys = raw_df.groupby(['Policy', 'Target'])["Keyword"].apply(lambda x : " - ".join(x.astype(str))).reset_index()
    dat_target_txtlength = raw_df.groupby(['Policy', 'Target']).first().reset_index()
    dat_number_of_keywords = raw_df.groupby(['Policy', 'Target']).count().reset_index()
    #merge both dataframes
    dat_target_level['Keyword'] = dat_target_join_keys['Keyword']
    dat_target_level['Textlength'] = dat_target_txtlength['Textlength']
    dat_target_level['Num_keys'] = dat_number_of_keywords['Count']
    #add Goal Column to DF
    #join SDG label as new column to target-lvel-dat, information coming from goal_df
    dat_target_level = sdg_references.join(dat_target_level.set_index('Target'), on='Target', how="inner")
    #drop target_ID column
    dat_target_level = dat_target_level.sort_values("Policy")
    #sort by policy and then by tar_id
    dat_target_level = dat_target_level.sort_values(['Policy', 'tar_ID'], ascending=[True,True])
    #add Policy ID column to df
    policy_ls = dat_target_level['Policy'].unique().tolist()
    policy_id_dict = {}
    for i in range(0, len(policy_ls)):
        policy_id_dict[policy_ls[i]] = i
    #match dict keys with df and add id as new column
    dat_target_level["ID"] = dat_target_level["Policy"].apply(lambda ID: policy_id_dict.get(ID))
    return dat_target_level


###########################################
#################################
########################
################



###############
########################
#################################
#########################################
#apply filter to drop unrelated targets
#using fixed textlength values for now as percentile distribution of textlength will not work reliably for small set of docs
#create list of percentile values from textlength column

def filter_data(df_target_level):
    #get list of unique textlength values
    dat_txtlength = df_target_level.groupby('Policy').first().reset_index()
    filter_0 = df_target_level.loc[(df_target_level['Textlength'] < 5_000)]
    filter_1 = df_target_level.loc[(df_target_level['Textlength'] > 5_000) &
                              (df_target_level['Textlength'] < 20_000) &
                              (df_target_level['Count'] > 1)]
    filter_2 = df_target_level.loc[(df_target_level['Textlength'] > 20_000) &
                              (df_target_level['Textlength'] < 100_000) &
                              ((df_target_level['Count'] >= 3) | (df_target_level['Num_keys'] > 2))]
    filter_3 = df_target_level.loc[(df_target_level['Textlength'] > 100_000) &
                              (df_target_level['Textlength'] < 300_000) &
                              ((df_target_level['Count'] >= 4) | (df_target_level['Num_keys'] > 3))]
    filter_4 = df_target_level.loc[(df_target_level['Textlength'] > 300_000) &
                              ((df_target_level['Count'] >= 5) | (df_target_level['Num_keys'] > 4))]
    filter_df = filter_0.append([filter_1, filter_2, filter_3, filter_4])
    filter_df = filter_df.iloc[filter_df.Policy.str.lower().argsort()]
    return filter_df



#######################################
#########################
###############
########



###########
####################
##############################
############################################


def get_target_overview(df, sdg_references):
    #groupby SDG column and count
    target_df = df.groupby('Target')["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    #keep only necessary columns
    target_df = target_df[["Target", "Count"]]
    #add SDG label
    target_df = sdg_references.join(target_df.set_index('Target'), on='Target', how="inner")
    return target_df


############################################
################################
#######################
################



################
########################
################################
############################################

def find_undetected_targets(df, sdg_references):
    detected_targets = df.groupby('Target').count().reset_index()
    #keep only necessary columns
    detected_targets = detected_targets[["Target", "Count"]]
    #do join with SDG list, but use outer method to get undetected
    undetected_targets = pd.concat([sdg_references['Target'],detected_targets['Target']]).drop_duplicates(keep=False)
    #make series df and assign column names
    undetected_targets = undetected_targets.to_frame()
    undetected_targets = sdg_references.join(undetected_targets.set_index('Target'), on='Target', how="inner")
    # undetected_targets.columns = ['Target', 'Goal']
    undetected_targets = undetected_targets.reset_index(drop=True)
    return undetected_targets


###########################################
##############################
#######################
##################




###################
##########################
#################################
##############################################

def aggregate_to_goals(goal_level_count, sdg_references):
    #drop target-related columns from sdg_references
    sdg_references = sdg_references[['Goal', 'goal_id', 'goal_description']]
    # choose results from goal level count output
    #group rows by policy and by target and sum count
    dat_goal_level = goal_level_count.groupby(['Policy', 'Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    dat_goal_join_keys = goal_level_count.groupby(['Policy', 'Goal'])["Keyword"].apply(lambda x : " - ".join(x.astype(str))).reset_index()
    dat_goal_txtlength = goal_level_count.groupby(['Policy', 'Goal']).first().reset_index()
    dat_number_of_keywords = goal_level_count.groupby(['Policy', 'Goal']).count().reset_index()
    #merge both dataframes
    dat_goal_level['Keyword'] = dat_goal_join_keys['Keyword']
    dat_goal_level['Textlength'] = dat_goal_txtlength['Textlength']
    dat_goal_level['Num_keys'] = dat_number_of_keywords['Count']
    dat_goal_level = dat_goal_level.sort_values("Policy")
    #add Goal ID and Goal Description
    dat_goal_level = sdg_references.join(dat_goal_level.set_index('Goal'), on='Goal', how="inner")
    dat_goal_level.drop_duplicates(inplace=True, ignore_index=True)
    dat_goal_level = dat_goal_level.sort_values("Policy")
    # use filter to drop rows < 2 (or another criteria??)
    # dat_goal_level = dat_goal_level.loc[dat_goal_level['Count'] > 1]
    return dat_goal_level

###########################################
##############################
#######################
##################



###################
##########################
#################################
##############################################
#merge counts from aggregated target-level and aggregated goal-level

def get_goal_overview(df_filtered, dat_goal_level, sdg_references):
    #drop target-related columns from sdg_references
    sdg_references = sdg_references[['Goal', 'goal_id', 'goal_description']]
    #create new df with policy and goals only, drop duplicates
    df = df_filtered.groupby(['Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    #select certain colums
    dat_goal_level = dat_goal_level[['Goal', 'Count']]
    dat_goal_level = dat_goal_level.groupby(['Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    #merge with dfs
    merged_df = df.append(dat_goal_level, ignore_index=True)
    #group by goal and sum count again
    merged_df = merged_df.groupby(['Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    merged_df = sdg_references.join(merged_df.set_index('Goal'), on='Goal', how="inner")
    merged_df.drop_duplicates(inplace=True, ignore_index=True)
    merged_df = merged_df.sort_values("goal_id")
    return merged_df


################################################
###############################
######################
##############


###################
##########################
#################################
##############################################

def group_byNAme_and_get_goaloverview(target_df, goal_df, sdg_references):
    #group target results by Policy and Goal and aggregate counts
    target_df = target_df.groupby(['Policy', 'Goal']).agg({'Count': ['sum']}).reset_index()
    #the above line creates tuples as column names so for append later to work columns need to be renamed
    target_df.columns = ['Policy', 'Goal', 'Count']
    #subset columns before append
    goal_df = goal_df[['Policy', 'Goal', 'Count']]
    #append both results
    grouped_df = goal_df.append(target_df, ignore_index=True)
    #group again by Policy and Goal and aggregate counts for final df
    grouped_df = grouped_df.groupby(['Policy', 'Goal']).agg({'Count': ['sum']}).reset_index()
    #adding Goal ID column
    #subset sdg references first
    sdg_references = sdg_references[['Goal','goal_id']].drop_duplicates().reset_index()
    #rename columns because of multiindex
    grouped_df.columns = ['Policy', 'Goal', 'Count']
    grouped_df = sdg_references.join(grouped_df.set_index('Goal'), on='Goal', how="inner")
    #group by policy and sort by goal id
    grouped_df = grouped_df.groupby('Policy').apply(lambda x: x.sort_values('goal_id'))
    return grouped_df

################################################
###############################
######################
##############



###################
##########################
#################################
##############################################
#merge counts from aggregated target-level and aggregated goal-level

def get_number_of_policies_per_goal(df_filtered, dat_goal_level):
    #create new df with policy and goals only, drop duplicates
    df = df_filtered[['Policy','Goal']]
    df = df.drop_duplicates().reset_index()
    #select certain colums
    dat_goal_level = dat_goal_level[['Policy','Goal']]
    #merge with dfs
    df_merged = df.append(dat_goal_level, ignore_index=True)
    #drop duplicate rows
    df_merged = df_merged.drop_duplicates().reset_index()
    return_df = df_merged.groupby(['Goal']).count().reset_index()
    return_df = return_df[['Goal', 'Policy']]
    #merge all policies in one string
    goal_df_policies = df_merged.groupby(['Goal'])["Policy"].apply(lambda x: " - ".join(x.astype(str))).reset_index()
    return_df['Policies'] = goal_df_policies['Policy']
    return_df.columns = ['Goal', 'Numer_of_Policies', 'Policies']
    return return_df

################################################
###############################
######################
##############


###############
########################
#####################################
################################################

#specify filename and dirpath is you don't want to call GUI
# def create_json_files_for_bubbleplots(target_df, aggregated_goal_counts): #filename = None, output_path = None
#     target_df['Target'] = 'Target ' + target_df['Target'].astype(str)
#     target_df.Count = target_df.Count.astype(int)
#     aggregated_goal_counts.Count = aggregated_goal_counts.Count.astype(int)
#     #rename both df's for JSON output
#     goal_subset = aggregated_goal_counts.rename(columns={'Goal': 'name', 'Count': 'size'}, inplace=False)
#     target_subset = target_df.rename(columns={'Target': 'name', 'Count': 'size', 'Goal': 'Goal'}, inplace=False)
#     # creating list of dicts for each SDG
#     gb = target_subset.groupby('Goal', sort=False)
#     ls = [gb.get_group(x) for x in gb.groups]
#     dict_ls = []
#     for index, group in enumerate(ls):
#         label = ls[index]['Goal'].unique()
#         # print(label)
#         # get size for SDG bubble
#         size = goal_subset.loc[index]['size']
#         # print(size)
#         # create list of dicts for each SDG
#         tmp_ls = []
#         for row_dict in ls[index].to_dict(orient="records"):
#             tmp_ls.append(row_dict)
#         # make final dict with label, size, list of dicts and append to dict_list
#         tmp_dict = {'name': label[0], 'size': int(size), 'children': tmp_ls}
#         dict_ls.append(tmp_dict)
#     final_dict = {'name': "sdgs", 'children': dict_ls}
#     # if output_path == None:
#     #     root = Tk()
#     #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
#     # if filename == None:
#     #     filename = str("bubbleplot_" + str(date) + ".json")
#     # complete_path = os.path.join(output_path, filename)
#     # with open(complete_path, 'w') as fp:
#     #     json.dump(final_dict, fp)
#     # # return print("JSON files have been exported to: " + complete_path)
#     return final_dict


################################################
######################################
#########################
################


def create_json_files_for_bubbleplots(target_df, aggregated_goal_counts): #filename = None, output_path = None
    target_df['Target'] = 'Target ' + target_df['Target'].astype(str)
    target_df.Count = target_df.Count.astype(int)
    aggregated_goal_counts.Count = aggregated_goal_counts.Count.astype(int)
    #rename both df's for JSON output
    goal_subset = aggregated_goal_counts.rename(columns={'Goal': 'name', 'Count': 'size'}, inplace=False)
    target_subset = target_df.rename(columns={'Target': 'name', 'Count': 'size', 'Goal': 'Goal'}, inplace=False)
    # creating list of dicts for each SDG
    # gb = target_subset.groupby('Goal', sort=False)
    # ls = [gb.get_group(x) for x in gb.groups]
    dict_ls = []
    for i in range(0, len(goal_subset)):
        label = goal_subset['name'][i]
        #subset target data
        temp_target_df = target_subset[target_subset['Goal'] == label]
        #drop first index column to not export to json
        temp_target_df.drop(temp_target_df.columns[0], axis = 1, inplace = True)
        # get size for SDG bubble
        size = goal_subset.iloc[i]['size']
        # create list of dicts for each SDG
        tmp_ls = []
        for row_dict in temp_target_df.to_dict(orient="records"):
            # print(row_dict)
            tmp_ls.append(row_dict)
        # make final dict with label, size, list of dicts and append to dict_list
        tmp_dict = {'name': label, 'size': int(size), 'children': tmp_ls}
        dict_ls.append(tmp_dict)
    final_dict = {'name': "sdgs", 'children': dict_ls}
    # if output_path == None:
    #     root = Tk()
    #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
    # if filename == None:
    #     filename = str("bubbleplot_" + str(date) + ".json")
    # complete_path = os.path.join(output_path, filename)
    # with open(complete_path, 'w') as fp:
    #     json.dump(final_dict, fp)
    # # return print("JSON files have been exported to: " + complete_path)
    return final_dict


################
############################
#########################################
###################################################
##takes df processed with add_further_info_to_df() as input
###outputs individual json files, 1 file = 1 policy

#specify dirpath argument if you don't want to call GUI for selecting output_folder
def create_json_files_for_sankey_charts(df): #output_path=None
    # if output_path == None:
    #     #first let user select output folder for json files
    #     root = Tk()
    #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
    #create list with unique policy names
    pol_ls = df.Policy.unique().tolist()
    for item in pol_ls:
        # print(pol_ls.index(item))
        nodes_ls = []
        links_ls = []
        final_dict = {}
        nodes_col = ['#3E3E3E']
        nodes_id = [0]
        links_source = []
        links_target = []
        links_val = []
        links_col = []
        temp_df = df.loc[df['Policy'] == item]
        temp_df.reset_index(drop=True, inplace=True)
        nodes_names = [temp_df.iloc[0]['Policy']]
        nodes_description = [temp_df.iloc[0]['target_description']]
        # print(temp_df)
        for ind in temp_df.index:
            nodes_names.append(temp_df['Target'][ind])
            nodes_col.append(temp_df['goal_color'][ind])
            nodes_id.append(int(ind + 1))
            nodes_description.append(temp_df['target_description'][ind])
            links_source.append(int(0))
            links_target.append(int(ind + 1))
            links_val.append(int(temp_df['Count'][ind]))
            links_col.append(temp_df['goal_color'][ind])
        nodes_ls = [
            {'node': nodes_id[i], 'name': nodes_names[i], 'color': nodes_col[i], 'description': nodes_description[i]}
            for i in range(len(nodes_names))]
        links_ls = [{'source': links_source[i], 'target': links_target[i], 'value': links_val[i], 'color': links_col[i]}
                    for i in range(len(links_source))]
        final_dict = {"nodes": nodes_ls, "links": links_ls}
        # filename = str(temp_df.iloc[0]['ID'] + 1) + '_' + temp_df.iloc[0]['Policy'] + '.json'
        # complete_path = os.path.join(output_path, filename)
        # with open(complete_path, 'w') as fp:
        #     json.dump(final_dict, fp)
    return final_dict

####################################################
#########################################
#############################
##################



################
############################
#########################################
###################################################
##make policy list ready for platform, use output from add_further_info_to_df as input df
##functions exports csv table with list of policies

def export_csv_for_policy_list(df, sdg_references): #filename=None, output_path=None
    #create unique policy names list
    pol_ls = list(df.Policy.unique())
    goal_ls = list(sdg_references.Goal.unique())
    #create list with column names for empty dataframe
    colnames_ls = ["ID", "Policy"]
    colnames_ls = colnames_ls + goal_ls + ["N. OF SDGs"]
    #create empty df from colnames_ls
    output_df = pd.DataFrame(columns=colnames_ls)
    #for each policy create new row in empty df
    for i in range(0, len(pol_ls)):
        #get list of detected goals per policy from input_df
        temp_df = df.loc[df['Policy'] == pol_ls[i]]
        #create list with row values to append to empty df
        to_append = [i+1, pol_ls[i]]
        #create list with 17 0'S
        goal_row = [""]*17
        # get list of matches between goal_ls and temp_df['Goal']
        temp_goals = list(temp_df.Goal.unique())
        for item in temp_goals:
            if item in goal_ls:
                goal_row[goal_ls.index(item)] = item
        #add goal_row to to-append
        to_append = to_append + goal_row + [len(temp_goals)]
        #append list as new row in empty df
        df_length = len(output_df)
        output_df.loc[df_length] = to_append
    #export final df as csv
    #choose output folder
    # if output_path == None:
    #     root = Tk()
    #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
    # if filename == None:
    #     filename = str("table-policies-sdgs_" + str(date) + ".csv")
    # full_path = os.path.join(output_path, filename)
    # #specify semicolon as delimiter for Diego's code to update platform
    # output_df.to_csv(full_path, sep=";", index=False, encoding='utf-8-sig')
    # output_df = output_df.iloc[output_df.Policy.str.lower().argsort()]
    # print(filename + " has been exported to: " + output_path)
    output_df = output_df.iloc[output_df.Policy.str.lower().argsort()]
    return output_df


####################################################
#########################################
#############################
##################


################
############################
#########################################
###################################################
##create function to create policy-coherence data and export table
##function checks which policies addressed the same targets


def create_policy_coherence_data(df, sdg_references): #filename_policy_coherence_dat=None, output_path=None
    #create df with 2 columns showing all possible combinations of targets
    target_list = sdg_references['Target'].tolist()
    target_combinations = pd.DataFrame(columns=['tar_1', 'tar_2'])
    for i in range(0, len(target_list)):
        tar_1 = [target_list[i]] * (len(target_list)-1)
        tar_2 = [x for x in target_list if x != target_list[i]]
        count_col = [0] *(len(target_list)-1)
        overlapping_policies = [""] *(len(target_list)-1)
        tar_dict = {'tar_1':tar_1, 'tar_2':tar_2, 'number_policies':count_col, 'Policies':overlapping_policies}
        to_append = pd.DataFrame(tar_dict)
        target_combinations = target_combinations.append(to_append)
    ##########
    ##########
    ##########
    #subset df for test purposes to save runtime
    # target_combinations = target_combinations.iloc[:1000, :]
    ###########
    ###########
    ###########
    for item in list(df.Policy.unique()):
        temp_df = df.loc[df['Policy'] == item]
        for i in range(0, len(target_combinations['tar_1'])):
            temp_targets = temp_df['Target'].tolist()
            row_ls = target_combinations.iloc[i,[0,1]]
            if all(x in temp_targets for x in row_ls) == True:
                target_combinations.iloc[i, 2] = target_combinations.iloc[i, 2] + 1
                target_combinations.iloc[i, 3] = str(target_combinations.iloc[i, 3] + " - " + str(temp_df['Policy'].iloc[0]))
    target_combinations = target_combinations.loc[target_combinations['number_policies'] > 1]
    #remame tar_1, column
    target_combinations.rename(columns={'tar_1':'Target'}, inplace=True)
    target_combinations = sdg_references.join(target_combinations.set_index('Target'), on='Target', how="inner")
    target_combinations.rename(columns={'Target':'tar_1'}, inplace=True)
    #remove " - " from beginning of Policies column
    target_combinations['Policies'] = target_combinations['Policies'].str[3:]
    #define proper datatypes before export
    target_combinations['number_policies'] = pd.to_numeric(target_combinations['number_policies'], downcast="integer")
    target_combinations['tar_1'] = target_combinations['tar_1'].astype(str)
    #define dtype to avoid wrong formats when using output again
    target_combinations.tar_1 = target_combinations.tar_1.astype(str)
    target_combinations.tar_2 = target_combinations.tar_2.astype(str)
    #prepare export to csv
    # if filename_policy_coherence_dat == None:
    #     filename_policy_coherence_dat = 'policy-coherence_' + str(date) + ".csv"
    # #create file dialogue to select output folder
    # if output_path == None:
    #     root = Tk()
    #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
    # full_path = os.path.join(output_path, filename_policy_coherence_dat)
    # #write to csv
    # target_combinations.to_csv(full_path, sep=";", index=False, encoding='utf-8-sig')
    # print(filename_policy_coherence_dat + " has been exported to: " + output_path)
    return target_combinations


####################################################
#########################################
#############################
##################


  
#########################
#############################
################################
####################################

#########################
#############################
################################
####################################


## function for filtering target dat by priority
def map_target_dat_to_priorities(target_df, sdg_references):
    #group by first priority column + aggregate to goal, within the grouped priority
    main_priority_df = target_df.groupby(['MAIN_priority', 'Goal']).agg({'Count': ['sum']}).reset_index()
    main_priority_df.rename(columns={'MAIN_priority': 'priority'}, inplace=True)
    #group by second priority + aggregate to goal, within the grouped priority
    sec_priority_df = target_df.groupby(['SEC_priority', 'Goal']).agg({'Count': ['sum']}).reset_index()
    sec_priority_df.rename(columns={'SEC_priority': 'priority'}, inplace=True)
    #append both dataframes
    priority_target_df = main_priority_df.append(sec_priority_df, ignore_index=True)
    #drop multi-level column index coming from groupby functions
    priority_target_df.columns = priority_target_df.columns.droplevel(1)
    priority_target_df = priority_target_df.groupby(['priority', 'Goal']).agg({'Count': ['sum']}).reset_index()
    priority_target_df.columns = priority_target_df.columns.droplevel(1)
    #add goal information from sdg_references to final output
    sdg_references = sdg_references.loc[:,['Goal', 'goal_id', 'goal_description', 'goal_color']]
    #drop duplicates
    sdg_references = sdg_references.drop_duplicates(ignore_index=True)
    priority_target_df = sdg_references.join(priority_target_df.set_index('Goal'), on='Goal', how="inner", lsuffix='_left',rsuffix='_right')
    #make goal_id int for sorting
    priority_target_df.goal_id = priority_target_df.goal_id.astype(int)
    priority_target_df = priority_target_df.sort_values(['priority', 'goal_id'],
                   ascending=[True, True])
    return priority_target_df

#####################################
################################
############################
#########################

#########################
#############################
################################
####################################


#function that takes filtered target dat + priority df as input to create bubblecharts
def create_json_for_priorities(filtered_targets):
    children_2nd_level = []
    for item in list(filtered_targets.priority.unique()):
        #subset dataframe by priority
        temp_df = filtered_targets.loc[filtered_targets['priority'] == item]
        temp_df.reset_index(drop=True, inplace=True)
        #rename columns for json export
        temp_df = temp_df.rename(columns={'Goal': 'name', 'Count': 'size'})
        #get sum of priority counts
        priority_size = temp_df['size'].sum()
        #make size and goal_id columns str for json export
        temp_df.loc[:,'size'] = temp_df['size'].astype(str)
        temp_df.loc[:,'goal_id'] = temp_df['goal_id'].astype(str)
        #get label for priority
        priority_name = temp_df.iloc[0]['priority']
        children_3rd_level = []
        #drop priority column from temp_df
        temp_df = temp_df.drop('priority', axis='columns')
        for i in range(0, len(temp_df['name'])):
            dict_3rd_level = temp_df.loc[i].to_dict()
            children_3rd_level.append(dict_3rd_level)
        dict_2nd_level = {'name':priority_name, 'size': str(priority_size), 'children':children_3rd_level}
        children_2nd_level.append(dict_2nd_level)
    final_dict = {"name": 'sdgs', "children": children_2nd_level}
    return final_dict



#####################################
################################
############################
#########################
 


##WHAT NEEDS TO BE DONE???

##in order to make code work with continuous updating of the policy mapping exercise
# several functions need to be updated according to the 2 categories used in the mapping
# legislative vs. non-legislative

#########################
#############################
################################
####################################


# def export_dataframes(target_df, filtered_df, target_overview_df, undetected_targets_df, goal_df, goal_overview_df,pol_per_goal_df): #filename_main_results=None, output_path=None
#     if filename_main_results == None:
#         filename_main_results = "processed_results_" + str(date) + ".xlsx"
#     if output_path == None:
#         root = Tk()
#         output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
#     full_path = os.path.join(output_path, filename_main_results)
#     writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
#     # export final output
#     target_df.to_excel(writer, sheet_name='aggregated_target_level')
#     filtered_df.to_excel(writer, sheet_name='filtered_target_dat')
#     target_overview_df.to_excel(writer, sheet_name='target_overview')
#     undetected_targets_df.to_excel(writer, sheet_name='undetected_targets')
#     goal_df.to_excel(writer, sheet_name='aggregated_goal_level')
#     goal_overview_df.to_excel(writer, sheet_name='goal_overview')
#     pol_per_goal_df.to_excel(writer, sheet_name="pol_per_goal")
#     writer.save()
#     return print("All dataframes were exported as: " + filename_main_results + " to: " + output_path)


#####################################
################################
############################
#########################