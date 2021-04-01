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
'#37e440','#0a97d9','#56c02b',
'#00689d','#19486a']
sdg_color = {label : color for label, color in zip(df['Name'].tolist(),color_ls)}

#####Define hierarchical bubbles based on data.
#def
# compute circle positions:
circles = crcf.circlify(
    df['Value'].tolist(), 
    show_enclosure=True, 
    target_enclosure=crcf.Circle(x=0, y=0, r=2)
)
#return

# Create just a figure and only one subplot
#def
fig, ax = plt.subplots(figsize=(15,15))

# Title
ax.set_title(f'SDGs in {Document}')

# Remove axes
ax.axis('off')

# Find axis boundaries
lim = max(
    max(
        abs(circle.x) + circle.r,
        abs(circle.y) + circle.r,
    )
    for circle in circles
)
plt.xlim(-lim, lim)
plt.ylim(-lim, lim)

# list of labels
labels = df['Name']

# print circles
for circle, label in zip(circles, labels):
    x, y, r = circle
    value=circle.ex['datum']
    ax.add_patch(plt.Circle((x, y), r*0.985, alpha=0.9, linewidth=1, facecolor=sdg_color[label], edgecolor="black"))
    plt.annotate(f'{label}\n{value}', (x,y) ,va='center', ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.2))

# if save_plot=True:
#     plt.savefig(svg_filepath_variable)
#return






#####Barplot#####
# Importing the matplotlib library
import numpy as np
import matplotlib.pyplot as plt
# Declaring the figure or the plot (y, x) or (width, height)
plt.figure(figsize=[15, 10])
# Data to be plotted
Rrp = [random.randint(1, 400) for i in range(1,18,1)]
RecPlan = [random.randint(1, 400) for i in range(1,18,1)]
EUSem = [random.randint(1, 400) for i in range(1,18,1)]
# # Using numpy to group 3 different data with bars
X = np.arange(len(Rrp))
# # Passing the parameters to the bar function, this is the main function which creates the bar plot
# # Using X now to align the bars side by side
plt.bar(X, Rrp, color = sdg_color.values(), alpha = 1, width = 0.25)    
plt.bar(X + 0.25, RecPlan, color = sdg_color.values(), alpha = 0.75, width = 0.25)
plt.bar(X + 0.5, EUSem, color = sdg_color.values(), alpha = 0.5, width = 0.25)
# Creating the legend of the bars in the plot
plt.legend(['Rrp', 'RecPlan', 'EuSem'])
# Overiding the x axis with the country names
plt.xticks([i + 0.25 for i in range(1,18,1)], df['Name'].tolist())
# Giving the tilte for the plot
plt.title("Count of references within the documents") #within {path.name}
# Namimg the x and y axis
#plt.xlabel('Countries')
plt.ylabel('Counts')
# Saving the plot as a 'png'
# if save_plot=True:
#     plt.savefig(svg_filepath_variable)
# Displaying the bar plot
plt.show()