import numpy as np
import pandas as pd
from natsort import index_natsorted, natsorted
import json, collections

def getsdgmetadata():
    """get sdgmetadata from UN SDG API and store them as a ordered dictionary"""
    
    sdg_indicators = pd.read_json('https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List')\
        .rename(columns={'goal': 'Goal', 'target':'Target', 
        'code':'Indicator','description':'Ind_desc'})
    sdg_goals = pd.read_json('https://unstats.un.org/SDGAPI/v1/sdg/Goal/List?includechildren=false')\
        .rename(columns={'code': 'Goal', 'title':'Goal_title', 'description':'Goal_desc'})[['Goal','Goal_title','Goal_desc']]
    sdg_targets = pd.read_json('https://unstats.un.org/SDGAPI/v1/sdg/Target/List?includechildren=false')\
        .rename(columns={'code': 'Target', 'goal':'Goal', 'description':'Target_desc'})[['Goal','Target','Target_desc']]

    sdg_goals = sdg_goals.sort_values(by=['Goal'], key=lambda x: np.argsort(index_natsorted(sdg_goals['Goal'])))
    sdg_targets = sdg_targets.sort_values(by=['Target'], key=lambda x: np.argsort(index_natsorted(sdg_targets['Target'])))
    sdg_indicators = sdg_indicators.sort_values(by=['Indicator'], key=lambda x: np.argsort(index_natsorted(sdg_indicators['Indicator'])))

    sdgmetadata_dict = collections.OrderedDict()

    for goalrow in sdg_goals.itertuples():
        sdg = f'SDG {goalrow.Goal}'
        sdgmetadata_dict[sdg]={'title': goalrow.Goal_title, 'description': goalrow.Goal_desc}
        sdgmetadata_dict[sdg]['targets'] = { f'Target {targetrow.Target}' : 
            { 'description': targetrow.Target_desc,
                'indicators': { f'{indicatorrow.Indicator}' : {'description':indicatorrow.Ind_desc} 
                for indicatorrow in sdg_indicators[sdg_indicators.Target==targetrow.Target].itertuples()}
            }
            for targetrow in sdg_targets[sdg_targets.Goal==goalrow.Goal].itertuples()}

    return sdgmetadata_dict

if __name__=='__main__':

    sdgmetadata_dict = getsdgmetadata()

    with open("sdgmetadata_dict.json", "w") as outfile:
        json.dump(sdgmetadata_dict, outfile)