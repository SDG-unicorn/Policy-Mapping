import random, re, json, pathlib, logging, time, argparse, pprint 
import pandas as pd
import numpy as np
import circlify as crcf
import matplotlib.pyplot as plt

##### Definition of color maps for goals and targets
sdg_names = [f'SDG {count}' for count in range(1,18,1)]
sdg_color_ls = ['#e5243b','#dda63a','#4c9f38',
'#c5192d','#ff3a21','#26bde2',
'#fcc30b','#a21942','#fd6925',
'#dd1367','#fd9d24','#bf8b2e',
'#3F7E44','#0a97d9','#56c02b',
'#00689d','#19486a']
goal_colors = {label : color for label, color in zip(sdg_names,sdg_color_ls)}

target_list=['1.1', '1.2', '1.3', '1.4', '1.5', '1.a', '1.b',
 '2.1', '2.2', '2.3', '2.4', '2.5', '2.a', '2.b', '2.c',
 '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.9', '3.a', '3.b', '3.c', '3.d',
 '4.1', '4.2', '4.3', '4.4', '4.5', '4.6', '4.7', '4.a', '4.b', '4.c',
 '5.1', '5.2', '5.3', '5.4', '5.5', '5.6', '5.a', '5.b', '5.c',
 '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.a', '6.b',
 '7.1', '7.2', '7.3', '7.a', '7.b',
 '8.1', '8.2', '8.3', '8.4', '8.5', '8.6', '8.7', '8.8', '8.9', '8.10', '8.a', '8.b',
 '9.1', '9.2', '9.3', '9.4', '9.5', '9.a', '9.b', '9.c',
 '10.1', '10.2', '10.3', '10.4', '10.5', '10.6', '10.7', '10.a', '10.b', '10.c',
 '11.1', '11.2', '11.3', '11.4', '11.5', '11.6', '11.7', '11.a', '11.b', '11.c',
 '12.1', '12.2', '12.3', '12.4', '12.5', '12.6', '12.7', '12.8', '12.a', '12.b', '12.c',
 '13.1', '13.2', '13.3', '13.a', '13.b',
 '14.1', '14.2', '14.3', '14.4', '14.5', '14.6', '14.7', '14.a', '14.b', '14.c',
 '15.1', '15.2', '15.3', '15.4', '15.5', '15.6', '15.7', '15.8', '15.9', '15.a', '15.b', '15.c',
 '16.1', '16.2', '16.3', '16.4', '16.5', '16.6', '16.7', '16.8', '16.9', '16.10', '16.a', '16.b',
 '17.1', '17.2', '17.3', '17.4', '17.5', '17.6', '17.7', '17.8', '17.9', '17.10', '17.11', '17.12', '17.13', '17.14', '17.15', '17.16', '17.17', '17.18', '17.19']

target_colors = { target : goal_colors[f"SDG {target.split('.')[0]}"] for target in target_list}

##### Mocke data for goals and targets

filename='ES_RRP'

res_path = pathlib.Path('./output/ES_RRP_/output/6-results/results_.xlsx')

mock_target_df = pd.read_excel(res_path,sheet_name='target_dat') #pd.DataFrame({
#     'Name': target_list,
#     'Value': [np.random.randint(0, 100) for i in target_list]
# })
mock_target_df=mock_target_df[['Target','Count']]
mock_target_df.rename(columns={"Target": "Name", "Count": "Value"}, inplace=True)
mock_target_df =  mock_target_df[mock_target_df['Value'] != 0]

mock_goals = pd.read_excel(res_path,sheet_name='goal_overview')
mock_goals = mock_goals['Count']

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


##### Goal Barplot for 1 or more groups #####

def sdg_barplot(sdg_item, color_dict, outfile=None):
    
    params_dict={'resolution':[15, 10],'plot_title' : '',
    'alpha':0.95, 'width' : 0.9, 'yval_offset' : 0.05,
    'xtick_labels' : [f'SDG {count}' for count in range(1,18,1)],'y_label': 'Count'}
    #if params_dict == None: if params dict diff none update keys/values with passed dictionary else use standard

    # Declaring the figure or the plot (y, x) or (width, height)
    fig = plt.figure(figsize=params_dict['resolution'])

    # Data to be plotted
    X = np.arange(len(sdg_item))

    if isinstance(sdg_item, list):  
        plt.bar(X, sdg_item, color = color_dict.values(), alpha = params_dict['alpha'], width = params_dict['width'])

        for x, y in zip(X,sdg_item):
            plt.annotate(str(y), xy=(x, y+params_dict['yval_offset']), ha='center', va='bottom', fontsize='large', fontweight='bold')
    
    elif isinstance(sdg_item,dict):
        for counter, key in enumerate(sdg_item.keys()):
            plt.bar(X+counter*params_dict['width']/(len(sdg_item)), 
            sdg_item[key], color = color_dict.values(), 
            alpha = params_dict['alpha']-(counter*params_dict['alpha']/(len(sdg_item))/1.5), 
            width = params_dict['width']/(len(sdg_item)))
            plt.legend(list(sdg_item.keys()))

   
    plt.xticks([i for i in range(0,17,1)], params_dict['xtick_labels'], fontsize='large', fontweight='bold', rotation=45)
    plt.yticks(fontsize='large', fontweight='bold')
    
    plt.title(params_dict['plot_title'], fontsize='large', fontweight='bold') #within {path.name}
    
    # plt.xlabel('SDGs')
    plt.ylabel(params_dict['y_label'], fontsize='large', fontweight='bold')
    if outfile != None:
        plt.savefig(f'{outfile}', dpi=300)
    return fig

sdg_barplot(mock_goals, goal_colors, outfile=f'{filename}_sdg_barlpot.png')

##### Goal or target horizontal barplot for 1 group #####

def sdg_hbars(sdg_item, sdg_labels, color_dict, outfile=None):
    
    params_dict={'resolution':[20, 30],'plot_title' : '',
    'alpha':0.95, 'width' : 0.9, 'yval_offset' : 0.05,
    'xtick_labels' : sdg_labels,'y_label': 'Count'}
    #if params_dict == None: if params dict diff none update keys/values with passed dictionary else use standard

    # Declaring the figure or the plot (y, x) or (width, height)
    fig = plt.figure(figsize=params_dict['resolution'])

    # Data to be plotted
    X = np.arange(len(sdg_item))

    plt.barh(X, sdg_item, color = [color_dict[label] for label in sdg_labels], 
    alpha = params_dict['alpha'])#, width = params_dict['width'])
   
    plt.yticks([i for i in range(0,len(params_dict['xtick_labels']),1)], params_dict['xtick_labels'])
    plt.xticks(fontsize='large', fontweight='bold')
    
    plt.title(params_dict['plot_title'], fontsize='large', fontweight='bold') #within {path.name}
    
    # plt.xlabel('SDGs')
    plt.xlabel(params_dict['y_label'], fontsize='large', fontweight='bold')
    if outfile != None:
        plt.savefig(f'{outfile}', dpi=300)
    plt.show()
    return fig

sdg_hbars(mock_target_df['Value'].tolist(), mock_target_df['Name'].tolist(), target_colors, outfile=f'{filename}_hbars.png')

##### Goal or target vertical barplot for 1 group #####

def sdg_vbars(sdg_item, sdg_labels, color_dict, outfile=None):
    
    params_dict={'resolution':[30, 20],'plot_title' : '',
    'alpha':0.95, 'width' : 0.9, 'yval_offset' : 0.05,
    'xtick_labels' : sdg_labels,'y_label': 'Count'}
    #if params_dict == None: if params dict diff none update keys/values with passed dictionary else use standard

    # Declaring the figure or the plot (y, x) or (width, height)
    fig = plt.figure(figsize=params_dict['resolution'])

    # Data to be plotted
    X = np.arange(len(sdg_item))

    plt.bar(X, sdg_item, color = [color_dict[label] for label in sdg_labels], alpha = params_dict['alpha'], 
    width = params_dict['width'])
   
    plt.xticks([i for i in range(0,len(params_dict['xtick_labels']),1)], params_dict['xtick_labels'], rotation=90)
    plt.yticks(fontsize='large', fontweight='bold')
    
    plt.title(params_dict['plot_title'], fontsize='large', fontweight='bold') #within {path.name}
    
    # plt.xlabel('SDGs')
    plt.ylabel(params_dict['y_label'], fontsize='large', fontweight='bold')
    if outfile != None:
        plt.savefig(f'{outfile}', dpi=300)
    plt.show()
    return fig

sdg_vbars(mock_target_df['Value'].tolist(), mock_target_df['Name'].tolist(), target_colors, outfile=f'{filename}_vbars.png')

def sdg_circbars(sdg_item, sdg_labels, color_dict, outfile=None):
    
    params_dict={'resolution':[20, 20],'plot_title' : '',
    'alpha':0.95, 'width' : 0.9, 'yval_offset' : 0.05,
    'xtick_labels' : sdg_labels,'y_label': 'Count', 
    'fontsize': 22, 'fontweight':850}

    # initialize the figure
    fig = plt.figure(figsize=params_dict['resolution'])
    ax = plt.subplot(111, polar=True)
    plt.axis('off')

    # Constants = parameters controling the plot layout:
    upperLimit = max(sdg_item)
    lowerLimit = min(sdg_item)
    labelPadding = 1.2

    # Compute max and min in the dataset
    # Let's compute heights: they are a conversion of each item value in those new coordinates
    # In our example, 0 in the dataset will be converted to the lowerLimit (10)
    # The maximum will be converted to the upperLimit (100)
    slope = (upperLimit - lowerLimit) / upperLimit
    heights = slope * np.array(sdg_item) #+ lowerLimit

    # Compute the width of each bar. In total we have 2*Pi = 360°
    width = 2*np.pi / len(sdg_item)

    # Compute the angle each bar is centered on:
    indexes = list(range(1, len(sdg_item)+1))
    angles = [element * width for element in indexes]
    
    # Draw bars
    bars = ax.bar(
        x=angles, 
        height=heights, 
        width=width, 
        bottom=lowerLimit,
        linewidth=2, 
        edgecolor="white",
        color="#61a4b2",
    )

    # Add labels
    for bar, angle, height, count, label in zip(bars, angles, heights, sdg_item , sdg_labels):

        bar.set_facecolor(color_dict[label])
        bar.set_alpha(0.95)

        # Labels are rotated. Rotation must be specified in degrees :(
        rotation = np.rad2deg(angle)

        # Flip some labels upside down
        alignment = ""
        if angle >= np.pi/2 and angle < 3*np.pi/2:
            alignment = "right"
            rotation = rotation + 180
        else: 
            alignment = "left"

        # Finally add the labels
        label_string=f'{label} ({count})'
        #y_pos= height - (labelPadding + len(label_string))

        ax.text(
            x=angle,
            s=label_string,  
            y= bar.get_height() + labelPadding, #upperLimit+2#
            ha=alignment, 
            va='center', 
            rotation=rotation, 
            rotation_mode="anchor",
            fontsize=params_dict['fontsize'], 
            fontweight=params_dict['fontweight']
            )
    if outfile != None:
        plt.savefig(f'{outfile}', dpi=300)
    plt.show()
    return fig

sdg_circbars(mock_target_df['Value'].tolist(), mock_target_df['Name'].tolist(), target_colors, outfile=f'{filename}_circbars.png')