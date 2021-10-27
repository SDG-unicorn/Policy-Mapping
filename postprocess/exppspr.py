import pandas as pd

def make_polpridf(results_df, pp_def):
    """
    Make a dataframe with SDG targets aligned with political prorities.
    This dataframe is the input for make_polpribubbleplot.
    """
    results_df["Target"]=results_df["Target"].astype(str)
    pp_def["Target"]=pp_def["Target"].astype(str)

    results_df=pd.merge(results_df, pp_def, on='Target', how='left')    
    results_df=results_df.drop(['Goal_y','goal_id','Unnamed: 0','tar_ID'],axis=1)

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
            polpri_dict["size"]=count
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
                    goal_dict["size"]=count
                    goal_dict["children"] = None
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
    sdg_bubbledict={"name": "sdgs", "children": None}
    goal_ls=[]

    goals=results_df.groupby(by=["Goal"]).sum()

    for goal, count in zip(goals.index.tolist(), goals['Sum_of_keys']):
        goal_dict={}
        if count > 0:
            goal_dict["name"]=goal
            goal_dict["size"]=count
            goal_dict["children"] = None
            goal_ls.append(goal_dict)
        else:
            continue


    for goal in goal_ls:
        target_ls=[]

        if goal["size"] >0:
            targetdf = results_df[results_df.Goal == goal["name"]]

            for target, count in zip(targetdf['Target'], targetdf['Sum_of_keys']):
                
                if count == 0:
                    continue
                
                elif str(target.split('.')[-1])=='0':
                    floor = round(count // 10)
                    remainder = round(count % 10)
                    mock = [10 for _ in range(floor)]
                    mock.append(remainder)
                    # if floor==0 or floor==1: #to troubleshoot
                    #     mock.append(remainder)
                    # elif mock[0]==10 and len(mock)==1:
                    #     mock.append(remainder)
                    # elif len(mock)>1:
                    #     mock[-1]=remainder
                    # print(f'Target {target}', int(count))
                    # print(floor, remainder)
                    # print(mock)

                    for item in mock:
                        target_dict={}
                        target_dict["name"]='Target 0'
                        target_dict["size"]=item
                        target_ls.append(target_dict)

                else:
                    target_dict={}
                    target_dict["name"]=f'Target {target}'
                    target_dict["size"]=count
                    target_ls.append(target_dict)
            
            goal['children']=target_ls
        
        else:
            continue

    sdg_bubbledict['children']=goal_ls
    
    return sdg_bubbledict