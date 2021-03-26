import pathlib , argparse, json
import datetime as dt
import pandas as pd
# from tkinter import filedialog
# from tkinter import *
# from nltk import tokenize

#######################################################
#######################################################
######  SET OPTIONS AND READ IN RELEVANT DATA  ########
#######################################################
#######################################################

parser = argparse.ArgumentParser(description="""Aggregate mapping results.""")
parser.add_argument('-i', '--input', help='Input file')
parser.add_argument('-o', '--output', help='Output directory', default='cwd')
parser.add_argument('-at', '--add_timestamp', help='Add a timestamp to output directory', type=bool, default=True)

args = parser.parse_args()

#get current time
date = dt.datetime.now().isoformat(timespec='seconds').replace(':','').replace('T','_T')

#for testing/checking df outputs
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)

#print all columns
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

input_dir=pathlib.Path(args.input)

#read python output
dat_raw = pd.read_excel(input_dir, sheet_name="Target_raw_count")
#developing countries rows not needed for DEVCO tool
#uncomment lines below if you need results from dev_countries count
# dat_dev_countries = pd.read_excel("results/raw/mapping_EC_Models_docs_2021-01-27_T102743.xlsx", sheet_name="Dev_countries_raw_count")
# #merge both df's
# dat_raw = dat_raw.append(dat_dev_countries).reset_index()
if args.output == 'cwd':
    out_dir = input_dir.parent / 'aggregated_and_filtered'
else:
    out_dir = pathlib.Path(args.output) / f'{input_dir.parent}_aggregated_and_filtered'

out_dir.mkdir(mode=0o777, parents=True, exist_ok=True)

#read in results from goal count
goal_counts = pd.read_excel(input_dir, sheet_name="Goal_raw_count")
# #as keyword detection does not work yet on detecting goal 1,2,3,etc. detected Keyword " goal " needs to be removed from the results
# goal_counts = goal_counts.loc[goal_counts['Keyword'] != ' goal ']

# read in table with list of SDG targets and Goals labels
# pay attention as goal_df is called in several functions without being used as input argument. 
# MM Please never do something like this, even if you document it. 
goal_df = pd.read_excel("goal_target_list.xlsx", sheet_name="Sheet1")
#read in descriptions of sdgs
target_texts = pd.read_csv('SDG-targets.csv')
#rename target column for merge later on
target_texts.rename(columns={'target': 'Target'}, inplace=True)

#list with SDG texts
goal_texts = ["No poverty", "Zero Hunger", "Good health and well-being", "Quality education",
                                 "Gender equality", "Clean water and sanitation", "Affordable and clean energy",
                                 "Decent work and economic growth", "Industry, innovation and infrastructure",
                                 "Reduced inequalities", "Sustainable cities and communities", "Responsible consumption and production",
                                 "Climate action", "Life below water", "Life on land", "Peace, justice and strong institutions",
                                 "Partnerships for the goals"]

#create dict for Goals + Texts
goal_ls = list(goal_df.Goal.unique())
goal_dict = dict(zip(goal_ls, goal_texts))


#######################################################
#######################################################
################  DEFINE FUNCTIONS  ##################
#######################################################
#######################################################

def stringify_id(pd_id_column, type=str):
    pd_id_column = pd_id_column.astype(type)
    return pd_id_column

######################
##############################
#####################################
#aggrgate to target level
#new column with number of keywords
# join all detected keywords in new column
def aggregate_to_targets(raw_df, goal_df):
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
    dat_target_level = goal_df.join(dat_target_level.set_index('Target'), on='Target', how="inner")
    #drop target_ID column
    #del dat_target_level['Target_ID']
    dat_target_level = dat_target_level.sort_values("Policy")
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

#create list of percentile values from textlength column

def filter_data(df_target_level):
    #get list of unique textlength values
    dat_txtlength = df_target_level.groupby('Policy').first().reset_index()
    filter_0 = df_target_level.loc[(df_target_level['Textlength'] < dat_txtlength.Textlength.quantile(0.15))]
    filter_1 = df_target_level.loc[(df_target_level['Textlength'] > dat_txtlength.Textlength.quantile(0.15)) &
                              (df_target_level['Textlength'] < dat_txtlength.Textlength.quantile(0.50)) &
                              (df_target_level['Count'] > 1)]
    filter_2 = df_target_level.loc[(df_target_level['Textlength'] > dat_txtlength.Textlength.quantile(0.50)) &
                              (df_target_level['Textlength'] < dat_txtlength.Textlength.quantile(0.95)) &
                              ((df_target_level['Count'] >= 3) | (df_target_level['Num_keys'] > 2))]
    filter_3 = df_target_level.loc[(df_target_level['Textlength'] > dat_txtlength.Textlength.quantile(0.95)) &
                              (df_target_level['Textlength'] < dat_txtlength.Textlength.quantile(0.99)) &
                              ((df_target_level['Count'] >= 4) | (df_target_level['Num_keys'] > 3))]
    filter_4 = df_target_level.loc[(df_target_level['Textlength'] > dat_txtlength.Textlength.quantile(0.99)) &
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


def get_target_overview(df, goal_df):
    #groupby SDG column and count
    target_df = df.groupby('Target').count().reset_index()
    #keep only necessary columns
    target_df = target_df[["Target", "Count"]]
    #add SDG label
    target_df = goal_df.join(target_df.set_index('Target'), on='Target', how="inner")
    #drop target_ID column
    target_df.drop(columns='Target_ID', inplace=True) # MM careful with delete statements: if you pass a mutable object you will affect the orginal object outside of the function
    return target_df


############################################
################################
#######################
################



################
########################
################################
############################################

def find_undetected_targets(df, goal_df):
    detected_targets = df.groupby('Target').count().reset_index()
    #keep only necessary columns
    detected_targets = detected_targets[["Target", "Count"]]
    #do join with SDG list, but use outer method to get undetected
    undetected_targets = pd.concat([goal_df['Target'],detected_targets['Target']]).drop_duplicates(keep=False)
    #make series df and assign column names
    undetected_targets = undetected_targets.to_frame()
    undetected_targets = goal_df.join(undetected_targets.set_index('Target'), on='Target', how="inner")
    undetected_targets.drop(columns='Target_ID', inplace=True)
    undetected_targets.columns = ['Target', 'Goal']
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

def aggregate_to_goals(goal_level_count):
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

def get_goal_overview(df_filtered, dat_goal_level, goal_df):
    #create new df with policy and goals only, drop duplicates
    df = df_filtered.groupby(['Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    #select certain colums
    dat_goal_level = dat_goal_level[['Goal', 'Count']]
    dat_goal_level = dat_goal_level.groupby(['Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    #merge with dfs
    df = df.append(dat_goal_level, ignore_index=True)
    #group by goal and sum count again
    goal_df = df.groupby(['Goal'])["Count"].apply(lambda x : x.astype(int).sum()).reset_index()
    return goal_df


################################################
###############################
######################
##############


###################
##########################
#################################
##############################################
#merge counts from aggregated target-level and aggregated goal-level

def get_number_of_policies_per_goal(df_filtered, dat_goal_level, goal_df):
    #create new df with policy and goals only, drop duplicates
    df = df_filtered[['Policy','Goal']]
    df = df.drop_duplicates().reset_index()
    #select certain colums
    dat_goal_level = dat_goal_level[['Policy','Goal']]
    #merge with dfs
    df = df.append(dat_goal_level, ignore_index=True)
    #drop duplicate rows
    df = df.drop_duplicates().reset_index()
    goal_df = df.groupby(['Goal']).count().reset_index()
    goal_df = goal_df[['Goal', 'Policy']]
    #merge all policies in one string
    goal_df_policies = df.groupby(['Goal'])["Policy"].apply(lambda x: " - ".join(x.astype(str))).reset_index()
    goal_df['Policies'] = goal_df_policies['Policy']
    goal_df.columns = ['Goal', 'Numer_of_Policies', 'Policies']
    return goal_df

################################################
###############################
######################
##############


###############
########################
#####################################
################################################

#specify filename and dirpath is you don't want to call GUI
def create_json_files_for_bubbleplots(target_df, goal_df): #filename=None ,output_path=None
    target_df['Target'] = 'Target ' + target_df['Target'].astype(str)
    #rename both df's for JSON output
    goal_subset = goal_df.rename(columns={'Goal': 'name', 'Policy': 'size'}, inplace=False)
    target_subset = target_df.rename(columns={'Target': 'name', 'Count': 'size', 'Goal': 'Goal'}, inplace=False)
    # creating list of dicts for each SDG
    gb = target_subset.groupby('Goal', sort=False)
    ls = [gb.get_group(x) for x in gb.groups]
    dict_ls = []
    for i in range(0, len(ls)):
        label = ls[i]['Goal'].unique()
        # print(label)
        # get size for SDG bubble
        size = goal_subset.iloc[i]['size']
        # print(size)
        # create list of dicts for each SDG
        tmp_ls = []
        for row_dict in ls[i].to_dict(orient="records"):
            tmp_ls.append(row_dict)
        # make final dict with label, size, list of dicts and append to dict_list
        tmp_dict = {'name': label[0], 'size': str(size), 'children': tmp_ls}
        dict_ls.append(tmp_dict)
    final_dict = {'name': "sdgs", 'children': dict_ls}
    # if output_path == None: # MM This is something to be done outside of the function. Would be better to have an ad hoc functions that calls this function
    #     root = Tk()
    #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
    # if filename == None:
    #     filename = str("bubbleplot_" + str(date) + ".json")
    # complete_path = os.path.join(output_path, filename)
    # with open(complete_path, 'w') as fp:
    #     json.dump(final_dict, fp)
    return final_dict



################################################
######################################
#########################
################



################
############################
#########################################
###################################################

#use this to create a simple df with all SDGs and corresponding Hex colors, needed for creating input files for knowSDGs visualisations
def create_color_code_table(goal_df):
    #create list with hex codes for visualisation
    hex_ls = ["#e5243b", "#dda63a", "#4c9f38", "#c5192d", "#ff3a21", "#26bde2", "#fcc30b", "#a21942", "#fd6925", "#dd1367",
              "#fd9d24", "#bf8b2e", "#37e440", "#0a97d9", "#56c02b", "#00689d", "#19486a"]
    goal_ls = list(goal_df.Goal.unique())
    #create df from both lists
    color_df = pd.DataFrame({'Goal':goal_ls, 'SDGcol':hex_ls})
    return color_df


################################################
######################################
#########################
################



################
############################
#########################################
###################################################
### add hex color code for data vis, add target id, policy id and target description to df#
#the output df serves as input for create_json_files_for_sankey_charts and export_csv_for_policy_list
#color_df is output from create_color_table

def add_further_info_to_df(df, color_df, goal_df):
    #use color code function to get df with hex colors
    #add color code to results
    sankey_df = df.merge(color_df, on='Goal', how='left')
    #add Policy ID
    policy_names = list(sankey_df.Policy.unique())
    id_ls = list(range(0,len(policy_names)))
    sankey_df = sankey_df.merge(pd.DataFrame({'Policy':policy_names, 'ID':id_ls}), on='Policy', how='left')
    #add Target_ID
    sankey_df = sankey_df.merge(goal_df, on='Target', how='left')
    #add Target Description from target_texts df, see beginning of script
    sankey_df = sankey_df.merge(target_texts, on='Target', how='left')
    sankey_df.drop(columns='Goal_y', inplace=True)
    sankey_df.drop(columns='goal', inplace=True)
    sankey_df.rename(columns={'Goal_x': 'Goal', 'Target_ID':'tar_ID'}, inplace=True)
    sankey_df = sankey_df.iloc[sankey_df.Policy.str.lower().argsort()]
    return sankey_df



####################################################
#########################################
#############################
##################

################
############################
#########################################
###################################################
##takes df processed with add_further_info_to_df() as input
###outputs individual json files, 1 file = 1 policy

#specify dirpath argument if you don't want to call GUI for selecting output_folder
def create_json_files_for_sankey_charts(df): # output_path=None
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
        nodes_description = [temp_df.iloc[0]['description']]
        # print(temp_df)
        for ind in temp_df.index:
            nodes_names.append(temp_df['Target'][ind])
            nodes_col.append(temp_df['SDGcol'][ind])
            nodes_id.append(int(ind + 1))
            nodes_description.append(temp_df['description'][ind])
            links_source.append(int(0))
            links_target.append(int(ind + 1))
            links_val.append(int(temp_df['Count'][ind]))
            links_col.append(temp_df['SDGcol'][ind])
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

def export_csv_for_policy_list(df, goal_df): # filename=None, output_path=None
    #create unique policy names list
    pol_ls = list(df.Policy.unique())
    goal_ls = list(goal_df.Goal.unique())
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
    #specify semicolon as delimiter for Diego's code to update platform
    # output_df.to_csv(full_path, sep=";", index=False, encoding='utf-8-sig')
    output_df = output_df.iloc[output_df.Policy.str.lower().argsort()]
    # print(filename + " has been exported to: " + output_path)
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


def create_policy_coherence_data(df, goal_df): #  filename=None, output_path=None
    #create df with 2 columns showing all possible combinations of targets
    target_list = goal_df['Target'].tolist()
    target_combinations = pd.DataFrame(columns=['tar_1', 'tar_2'])
    for i in range(0, len(target_list)):
        tar_1 = [target_list[i]] * (len(target_list)-1)
        tar_2 = [x for x in target_list if x != target_list[i]]
        count_col = [0] *(len(target_list)-1)
        overlapping_policies = [""] *(len(target_list)-1)
        Sdg_description = [""] *(len(target_list)-1)
        tar_dict = {'tar_1':tar_1, 'tar_2':tar_2, 'number_policies':count_col, 'Policies':overlapping_policies, 'Sdg_description':Sdg_description}
        to_append = pd.DataFrame(tar_dict)
        target_combinations = target_combinations.append(to_append)
    #subset df for test purposes to save runtime
    target_combinations = target_combinations.iloc[:100, :]
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
    target_combinations = goal_df.join(target_combinations.set_index('Target'), on='Target', how="inner")
    target_combinations = target_texts.join(target_combinations.set_index('Target'), on='Target', how="inner")
    target_combinations.drop(columns='goal', inplace=True) # del target_combinations['goal'] # del target_combinations['goal'] # target_combinations.drop(columns='goal', inplace=True)
    target_combinations.drop(columns='Target_ID', inplace=True) # del target_combinations['Target_ID'] # del target_combinations['Target_ID'] # 
    target_combinations.rename(columns={'Target':'tar_1','tar_2':'Target', 'description':'Target_Description', 'Goal':'Goal_tar_1'}, inplace=True)
    target_combinations = goal_df.join(target_combinations.set_index('Target'), on='Target', how="inner")
    target_combinations.drop(columns='Target_ID', inplace=True) # del target_combinations['Target_ID'] # del target_combinations['Target_ID'] # 
    target_combinations.rename(columns={'Target':'tar_2', 'Goal':'Goal_tar_2'}, inplace=True)
    target_combinations['Sdg_description'] = target_combinations['Goal_tar_2'].map(goal_dict)
    target_combinations = target_combinations[["tar_1", "tar_2", "number_policies","Policies","Goal_tar_1", "Goal_tar_2","Sdg_description", "Target_Description"]]
    #remove " - " from beginning of Policies column
    target_combinations['Policies'] = target_combinations['Policies'].str[3:]
    #define proper datatypes before export
    target_combinations['number_policies'] = pd.to_numeric(target_combinations['number_policies'], downcast="integer")
    target_combinations['tar_1'] = target_combinations['tar_1'].astype(str)
    #prepare export to csv
    # if filename == None:
    #     filename = str('policy-coherence_' + str(date) + ".csv")
    # #create file dialogue to select output folder
    # if output_path == None:
    #     root = Tk()
    #     output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
    # full_path = os.path.join(output_path, filename)
    # #write to csv
    # target_combinations.to_csv(full_path, sep=";", index=False, encoding='utf-8-sig')
    # print(filename + " has been exported to: " + output_path)
    return target_combinations


####################################################
#########################################
#############################
##################


##WHAT NEEDS TO BE DONE???

##in order to make code work with continuous updating of the policy mapping exercise
# several functions need to be updated according to the 2 categories used in the mapping
# legislative vs. non-legislative

#########################
#############################
################################
####################################


def export_dataframes(target_df, filtered_df, target_overview_df, undetected_targets_df, goal_overview_df,pol_per_goal_df, goal_df, filename=None, output_path=out_dir):
  
#   filename = f"processed_results_{date}.xlsx" if filename is None else filename
  
#   if output_path == None:
#       # root = Tk()
#       # output_path = filedialog.askdirectory(parent=root, initialdir="/", title='Please select output folder')
#     full_path = pathlib.Path(output_path) / filename
#   else:
#     full_path = pathlib.Path.cwd() / filename
    full_path = pathlib.Path(output_path) / f"processed_results_{date}.xlsx"
    writer = pd.ExcelWriter(full_path, engine='xlsxwriter')
    # export final output
    target_df.to_excel(writer, sheet_name='aggregated_target_level')
    filtered_df.to_excel(writer, sheet_name='filtered_target_dat')
    target_overview_df.to_excel(writer, sheet_name='target_overview')
    undetected_targets_df.to_excel(writer, sheet_name='undetected_targets')
    goal_df.to_excel(writer, sheet_name='aggregated_goal_level')
    goal_overview_df.to_excel(writer, sheet_name='goal_overview')
    pol_per_goal_df.to_excel(writer, sheet_name="pol_per_goal")
    writer.save()
    print(f"All dataframes were exported as:  {full_path}")
    return f"All dataframes were exported as:  {full_path}"


#####################################
################################
############################
#########################



#######################################################
#######################################################
################  EXECUTE FUNCTIONS  ##################
#######################################################
#######################################################

# 0.) Coerce Target columns to string

dat_raw['Target'] = stringify_id(dat_raw['Target'])

# 1.) aggregate to target-level --> export this to final results workbook
target_dat = aggregate_to_targets(dat_raw, goal_df)

# 2.) filter data according to specififed criteria --> export this to final results workbook
dat_filtered = filter_data(target_dat)

# 3.) get overview on target-level --> export this to final results workbook
target_overview_df = get_target_overview(target_dat, goal_df)

# 4.) get undetected targets --> export this to final results workbook
undetected_targets = find_undetected_targets(dat_filtered, goal_df)

# 5.)  aggregate goal counts to goal-level --> export this to final results workbook
goal_dat = aggregate_to_goals(goal_counts) #MM What if no goals are detected? We need to handle this scenario

# 6.) get goal_overview from target counts and goal counts --> export this to final results workbook
goal_overview = get_goal_overview(target_dat, goal_dat, goal_df)

# 7.) get goal overview but not with aggregated counts but with number of policies relating to a goal
policies_per_goal = get_number_of_policies_per_goal(target_dat, goal_dat, goal_df)

# 8.) create and export json files for bubblecharts on knowSDGs platform ## Fix this
#create_json_files_for_bubbleplots(target_overview_df, goal_overview)

# 9.) create df containing SDG labels and corresponding color hex codes
color_df = create_color_code_table(goal_df)

#MM 11,12,13 for the moment not needed

# 10.) add more info to policies, make sure to create color df first
#info_added_df = add_further_info_to_df(dat_filtered)

# 11.) export individual json files for each policy, input for individual sankey charts on knowSDGs platform
#create_json_files_for_sankey_charts(info_added_df)

# 12.) export csv table with list of policies (second viz on knowSDGs platform = List of Policies)
#policy_df = export_csv_for_policy_list(info_added_df)

# 13.) create and export policy coherence df (third viz knowSDGs platform)
# pol_coher_df=create_policy_coherence_data(dat_filtered, goal_df)#output_path=out_dir
# pol_coher_df.to_csv((pathlib.Path(out_dir) / 'policy_coherence.csv'), sep=";", index=False, encoding='utf-8-sig')

# 14.) exoport all df's on results to one Excel workbook
export_dataframes(target_dat, dat_filtered, target_overview_df, undetected_targets, goal_dat, goal_overview, policies_per_goal, output_path=out_dir)


#######################################################
#######################################################
#######################################################
#######################################################





#######################################################
#######################################################
#######################################################
##  WHAT ELSE NEEDS TO BE DONE ??? ####################
#######################################################
#######################################################

##for a proper update of the policy mapping in the platform the functions need to be adapted so that the category of each policy is also considered


#######################################################
#######################################################
#######################################################