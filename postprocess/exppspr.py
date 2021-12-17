import re, json
import pandas as pd
import natsort as ntst
from operator import itemgetter

#from collections import OrderedDict

def make_polpridf(results_df, pp_def):
    """
    Make a dataframe with SDG targets aligned with political prorities.
    This dataframe is the input for make_polpribubbleplot.
    """
    results_df["Target"]=results_df["Target"].astype(str)
    pp_def["Target"]=pp_def["Target"].astype(str)

    results_df=pd.merge(results_df, pp_def, on='Target', how='left')    
    results_df=results_df.drop(['Goal_y','goal_id','tar_ID'],axis=1)

    results_df=results_df.rename(columns={"Goal_x": "Goal"})

    main_df=results_df.groupby(by=['MAIN_priority','Goal']).sum().reset_index()
    main_df.rename(columns={'MAIN_priority': 'priority'}, inplace=True)

    sec_df=results_df.groupby(by=['SEC_priority','Goal']).sum().reset_index()
    sec_df.rename(columns={'SEC_priority': 'priority'}, inplace=True)

    priorities_df = main_df.append(sec_df, ignore_index=True)
    priorities_df = priorities_df.groupby(by=['priority','Goal']).sum().reset_index()
    
    return priorities_df

def make_polpribubbleplot(priorities_df):
    """
    Create a bubbleplot representing SDG targets aggragated by Goal and aligned to political priorities
    """
    polpri_bubbledict={"name": "sdgs", "children": None}
    polpri_ls=[]

    polpri=priorities_df.groupby(by=["priority"]).sum()

    for polpri, count in zip(polpri.index.tolist(), polpri['Sum_of_keys']):
        polpri_dict={}
        if count > 0:
            polpri_dict["name"]=polpri
            polpri_dict["size"]=int(count)
            polpri_dict["children"] = None
            polpri_ls.append(polpri_dict)
        else:
            continue

    for polpri in polpri_ls:
        goal_ls=[]

        if polpri["size"] >0 :
            goaldf = priorities_df[priorities_df.priority == polpri["name"]]

            for goal, count in zip(goaldf['Goal'], goaldf['Sum_of_keys']):
                goal_dict={}
                if count > 0:
                    goal_dict["name"]=goal
                    goal_dict["size"]=int(count)
                    goal_ls.append(goal_dict)                    
                else:
                    continue

        polpri['children']=goal_ls

    polpri_bubbledict['children']=polpri_ls

    return polpri_bubbledict

def make_sdgbubbleplot(results_df):
    """
    Create a bubbleplot representing SDG Golas and Targets.
    """
    #Later on, think about a way to make bubbleplot for PP

    #sdgdict = pp_def

    sdg_bubbledict={"name": "sdgs", "children": None}
    goal_ls=[]

    goals=results_df.groupby(by=["Goal"]).sum()

    for goal, count in zip(goals.index.tolist(), goals['Sum_of_keys']):
        goal_dict={}
        if count > 0:
            goal_dict["name"]=goal
            goal_dict["size"]=int(count)
            goal_dict["children"] = None
            goal_ls.append(goal_dict)
        else:
            continue


    for goal in goal_ls:
        target_ls=[]

        if goal["size"] > 0:
            targetdf = results_df[results_df.Goal == goal["name"]]

            for target, count in zip(targetdf['Target'], targetdf['Sum_of_keys']):
                
                if (count == 0): #or (str(target.split('.')[-1])=='0'):
                    continue                
                else:
                    target_dict={}
                    target_dict["size"]=int(count)

                    if str(target.split('.')[-1])=='0':                        
                        target_dict["name"]=f"SDG {target.split('.')[0]}_undetected"
                    else:
                        target_dict["name"]=f'Target {target}'

                    #move SDG XX_undetected at the end of the dict:
                    #see https://docs.python.org/3/library/collections.html#collections.OrderedDict.move_to_end
                    target_ls.append(target_dict)

            if 'undetected' in target_ls[0]['name']:
                target_ls.append(target_ls[0])
                target_ls.pop(0)

            goal['children']=target_ls
        
        else:
            continue

    sdg_bubbledict['children']=ntst.natsorted(goal_ls, key=itemgetter(*['name'])) 
    
    return sdg_bubbledict
    
def maketermcounttable(count_df, term_df):
    '''
    Make a table listing SDG terms and their counts.
    '''
    mapping_df=pd.DataFrame()
    
    for row1, row2 in zip(count_df.itertuples(), term_df.itertuples()):
        count_df=pd.DataFrame(data={'Count':row1,'Terms':row2}).iloc[3:]
        count_df['Goal'] = row1.Goal
        count_df['Target'] = row1.Target
        count_df = count_df.reindex(columns=['Goal','Target','Count','Terms'])   
        count_df.fillna(0, inplace=True)
        count_df = count_df[count_df.Count > 0]
        mapping_df = pd.concat([mapping_df, count_df])
    
    mapping_df.reset_index(drop=True, inplace=True)
    return mapping_df

with open('./postprocess/sdgmetadata_dict.json',) as f:
    sdgmetadata_dict = json.load(f)

def makeindicatorsjson(resultstotal_df, metadata_dict='Default'):
    '''Make a json file containing relevant indicators for the detected targets'''
    if metadata_dict=='Default':
        metadata_dict = sdgmetadata_dict
        
    
    indicators_dict = {"name": "sdgs", "goals": []}

    goals = ntst.natsorted(list(set(resultstotal_df['Goal'].values.tolist())))

    for goal in goals:
        goal_dict = {'name': goal, 'title':metadata_dict[goal]['title'], 'description':metadata_dict[goal]['description'],
        'targets' : []}
        indicators_dict['goals'].append(goal_dict)
    
        for row in resultstotal_df[resultstotal_df['Goal']==goal].itertuples():
                
            target_dict={}
            target = f'Target {row.Target}'
            target_dict['name'] = target

            mock_target = re.match(r'Target \d{1,2}.0', target)
            
            if mock_target:
                target_dict['description'] = metadata_dict[goal]['description']
            else:
                target_dict['description'] = metadata_dict[goal]['targets'][target]['description']
            
            target_dict['indicators'] = {'un':[]}

            for unind in row.UN_Indicators:
                if unind:
                    unind_dict={
                        'name':unind, 
                        'description':metadata_dict[goal]['targets'][target]['indicators'][unind]['description']
                    }
                    target_dict['indicators']['un'].append(unind_dict)

            goal_dict['targets'].append(target_dict)      

    return indicators_dict