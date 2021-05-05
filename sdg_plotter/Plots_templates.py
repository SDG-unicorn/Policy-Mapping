import random, re, json, pathlib, logging, time, argparse, pprint 
import pandas as pd
import numpy as np
import circlify as crcf
import matplotlib.pyplot as plt

#####Bubbleplot#####
##### Create mock data

Document = 'The European Green Deal' 

df = pd.DataFrame({
    'Name': [f'SDG {count}' for count in range(1,18,1)],
    'Value': [random.randint(1, 400) for i in range(1,18,1)]
})

color_ls = ['#e5243b','#dda63a','#4c9f38',
'#c5192d','#ff3a21','#26bde2',
'#fcc30b','#a21942','#fd6925',
'#dd1367','#fd9d24','#bf8b2e',
'#3F7E44','#0a97d9','#56c02b',
'#00689d','#19486a']
sdg_color = {label : color for label, color in zip(df['Name'].tolist(),color_ls)}

# #####Define hierarchical bubbles based on data.
# #def
# # compute circle positions:
# circles = crcf.circlify(
#     df['Value'].tolist(), 
#     show_enclosure=True, 
#     target_enclosure=crcf.Circle(x=0, y=0, r=2)
# )
# #return

# # Create just a figure and only one subplot
# #def
# fig, ax = plt.subplots(figsize=(15,15))

# # Title
# ax.set_title(f'SDGs in {Document}')

# # Remove axes
# ax.axis('off')

# # Find axis boundaries
# lim = max(
#     max(
#         abs(circle.x) + circle.r,
#         abs(circle.y) + circle.r,
#     )
#     for circle in circles
# )
# plt.xlim(-lim, lim)
# plt.ylim(-lim, lim)

# # list of labels
# labels = df['Name']

# # print circles
# for circle, label in zip(circles, labels):
#     x, y, r = circle
#     value=circle.ex['datum']
#     ax.add_patch(plt.Circle((x, y), r*0.985, alpha=0.9, linewidth=1, facecolor=sdg_color[label], edgecolor="black"))
#     plt.annotate(f'{label}\n{value}', (x,y) ,va='center', ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.2))

# # if save_plot=True:
# #     plt.savefig(svg_filepath_variable)
# #return



sdg_dict = {'whole':[8,205,46,8,2,105,17,97,282,2,18,109,233,89,210,23,31],
'jrc':[79,436,234,231,19,171,329,706,1959,60,427,450,996,104,230,343,106],
'f2f':[51,6,45,166,33,16,126,126,49,37,58,10,109,3,7,46,9]
}
whole=[8,205,46,8,2,105,17,97,282,2,18,109,233,89,210,23,31]
jrc=[79,436,234,231,19,171,329,706,1959,60,427,450,996,104,230,343,106]
f2f=[51,6,45,166,33,16,126,126,49,37,58,10,109,3,7,46,9]


#####Barplot#####
# Importing the matplotlib library
import numpy as np
import matplotlib.pyplot as plt
def sdg_barlpot(sdg_item, outfile=None):

    
    params_dict={'resolution':[15, 10],'plot_title' : '',
    'alpha':1, 'width' : 1,
    'xtick_labels' : [f'SDG {count}' for count in range(1,18,1)],'y_label': 'Count'}
    #if params_dict == None: if params dict diff none update keys/values with passed dictionary else use standard

    # Declaring the figure or the plot (y, x) or (width, height)
    fig = plt.figure(figsize=params_dict['resolution'])

    # Data to be plotted
    X = np.arange(17)

    if isinstance(sdg_item, list):  
        plt.bar(X, sdg_item, color = sdg_color.values(), alpha = params_dict['alpha'], width = params_dict['width'])
    
    elif isinstance(sdg_item,dict):
        for counter, key in enumerate(sdg_item.keys()):
            plt.bar(X+counter*params_dict['width']/(len(sdg_item)), 
            sdg_item[key], color = sdg_color.values(), 
            alpha = params_dict['alpha']-(counter*params_dict['alpha']/(len(sdg_item))/1.5), 
            width = params_dict['width']/(len(sdg_item)))
            plt.legend(list(sdg_item.keys()))

   
    plt.xticks([i for i in range(0,17,1)], params_dict['xtick_labels'], fontsize='large', fontweight='bold', rotation=45)
    plt.yticks(fontsize='large', fontweight='bold')
    
    plt.title(params_dict['plot_title'], fontsize='large', fontweight='bold') #within {path.name}
    
    # plt.xlabel('SDGs')
    plt.ylabel(params_dict['y_label'], fontsize='large', fontweight='bold')
    if outfile != None:
        plt.savefig(f'{outfile}', dpi=600)
    return fig

sdg_barlpot([random.randint(1, 400) for i in range(1,18,1)], outfile='test.png')