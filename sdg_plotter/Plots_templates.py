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




# whole=[8,205,46,8,2,105,17,97,282,2,18,109,233,89,210,23,31]
# jrc=[79,436,234,231,19,171,329,706,1959,60,427,450,996,104,230,343,106]

f2f=[1,88,7,0,0,3,7,5,12,1,0,42,23,8,15,0,8]


whole=[0,2,0,8,0,1,10,18,124,1,3,48,80,8,6,5,8]
rd_sl_rrp=[0,1,0,3,0,0,6,12,88,1,2,17,35,0,0,5,4]
rd_sl_rrp_annex_EN=[0,1,0,5,0,1,4,6,36,0,1,31,45,8,6,0,4]

#####Barplot#####
# Importing the matplotlib library
import numpy as np
import matplotlib.pyplot as plt
# Declaring the figure or the plot (y, x) or (width, height)
plt.figure(figsize=[15, 10])
# Data to be plotted
#Rrp = [random.randint(1, 400) for i in range(1,18,1)]
#RecPlan = [random.randint(1, 400) for i in range(1,18,1)]
#EUSem = [random.randint(1, 400) for i in range(1,18,1)]
# # Using numpy to group 3 different data with bars
X = np.arange(len(whole))
# # Passing the parameters to the bar function, this is the main function which creates the bar plot
# # Using X now to align the bars side by side
#plt.bar(X, whole, color = sdg_color.values(), alpha = 1, width = 0.75)    
plt.bar(X, f2f, color = sdg_color.values(), alpha = 0.95, width = 0.5)
#plt.bar(X + 0.5, rd_sl_rrp_annex_EN, color = sdg_color.values(), alpha = 0.75, width = 0.5)
# Creating the legend of the bars in the plot
#plt.legend(['maindoc+annex', 'rd_sl_rrp', 'rd_sl_rrp_annex'])
# Overiding the x axis with the country names
plt.xticks([i for i in range(0,17,1)], df['Name'].tolist(), fontsize='large', fontweight='bold', rotation=45)
plt.yticks(fontsize='large', fontweight='bold')
# Giving the tilte for the plot
plt.title("Mentions", fontsize='large', fontweight='bold') #within {path.name}
# Namimg the x and y axis
#plt.xlabel('Countries')
plt.ylabel('Counts',fontsize='large', fontweight='bold')
plt.savefig('f2f.svg', dpi=600)
# Saving the plot as a 'png'
# if save_plot=True:
#     plt.savefig(svg_filepath_variable)
# Displaying the bar plot
plt.show()