import random, re, json, pathlib, logging, time, argparse, pprint 
import pandas as pd
import numpy as np
import circlify as crcf
import matplotlib.pyplot as plt
import matplotlib.image as img

##### Create global variables for plot

Document = 'The European Green Deal' 

sdg_names = [f'SDG {count}' for count in range(1,18,1)]
color_ls = ['#e5243b','#dda63a','#4c9f38',
'#c5192d','#ff3a21','#26bde2',
'#fcc30b','#a21942','#fd6925',
'#dd1367','#fd9d24','#bf8b2e',
'#3F7E44','#0a97d9','#56c02b',
'#00689d','#19486a']
sdg_colors = {label : color for label, color in zip(sdg_names,color_ls)}

sdg_logos= [f"logos/SDG_{str(count).zfill(2)}.png" for count in range(1,18,1)]

pp={}


#####Bubbleplot#####
#Create mock data for bubbleplot
sdg_bubble_mockdata = [
        {'id': 'Green Deal', 'datum': 6964195249, 'children' : [
              {'id' : "SDG 1", 'datum': 450448697,
                   'children' : [
                     {'id' : "Target 1.1", 'datum' : 308865000},
                     {'id' : "Target 1.2", 'datum' : 107550697},
                     {'id' : "Target 1.3", 'datum' : 34033000} 
                   ]},
              {'id' : "SDG 2", 'datum' : 278095425, 
                   'children' : [
                     {'id' : "Target 2.1", 'datum' : 192612000},
                     {'id' : "Target 2.2", 'datum' : 45349000},
                     {'id' : "Target 2.3", 'datum' : 40134425}
                   ]}],
        },
        {'id': 'Digital age', 'datum': 3564195249, 'children' : [
              {'id' : "SDG 3", 'datum' : 209246682,  
                   'children' : [
                     {'id' : "Target 3.1", 'datum' : 81757600},
                     {'id' : "Target 3.2", 'datum' : 65447374},
                     {'id' : "Target 3.3", 'datum' : 62041708}
                   ]},
              {'id' : "SDG 4", 'datum' : 311929000,  
                   'children' : [
                     {'id' : "Target 4.1", 'datum' : 154729000},
                     {'id' : "Target 4.2", 'datum' : 79221000},
                     {'id' : "Target 4.3", 'datum' : 77979000}
                   ]}],
        },
        {'id': 'Economy4People', 'datum': 4564195249, 'children' : [
              {'id' : "SDG 5", 'datum' : 2745929500,  
                   'children' : [
                     {'id' : "Target 5.1", 'datum' : 1336335000},
                     {'id' : "Target 5.2", 'datum' : 1178225000},
                     {'id' : "Target 5.3", 'datum' : 231369500}
                   ]},
              {'id' : "SDG 6", 'datum' : 3545929500,  
                   'children' : [
                     {'id' : "Target 6.1", 'datum' : 936335000},
                     {'id' : "Target 6.2", 'datum' : 1878225000},
                     {'id' : "Target 6.3", 'datum' : 271369500}
                   ]}]
        }
       ]

#####Define hierarchical bubbles based on data.
#def
# compute circle positions:
# Compute circle positions thanks to the circlify() function
circles = crcf.circlify(
    sdg_bubble_mockdata, 
    show_enclosure=False, 
    target_enclosure=crcf.Circle(x=0, y=0, r=1)
)
#return

# Create just a figure and only one subplot
fig, ax = plt.subplots(figsize=(14,14))

# Title
ax.set_title('Feh')

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

rf={1:0.975, 2:0.95, 3:0.925} #reduction factor

# Print circles at pp level:
for circle in circles:
    if circle.level != 1:
      continue
    x, y, r = circle
    label = circle.ex["id"]
    ax.add_patch( plt.Circle((x, y), r*rf[circle.level], alpha=0.25, linewidth=2, color='purple'))

# Print circles at goal level:
for circle in circles:
    if circle.level != 2:
      continue
    x, y, r = circle
    label = circle.ex["id"]
    ax.add_patch( plt.Circle((x, y), r*rf[circle.level], alpha=0.5, linewidth=2, color=sdg_colors[label]))

# Print circle at target level:
for circle in circles:
    if circle.level != 3:
      continue
    x, y, r = circle
    label = circle.ex["id"]
    color = re.sub(r'Target (\d{,2}).[a-z0-9]', r'SDG \1', label)
    label = label.replace('Target ','')
    ax.add_patch( plt.Circle((x, y), r*rf[circle.level], linewidth=0, color="white"))
    ax.add_patch( plt.Circle((x, y), r*rf[circle.level], alpha=0.5, linewidth=0, color=sdg_colors[color]))
    plt.annotate(label, (x,y ), ha='center', color="white")

# Print labels for the continents
for circle in circles:
    if circle.level not in (1,2):
      continue
    x, y, r = circle
    label = circle.ex["id"]
    if circle.level == 2:
        plt.annotate(label, (x,y ) ,va='center', ha='center', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round', pad=.125))
    elif circle.level == 1:
        plt.annotate(label, (x,y+r), ha='center', color="black")

plt.savefig('Bubbleplot.png', dpi=300)
plt.show()


# # reading png image file
# im = img.imread(sdg_logos[0])
  
# # show image
# plt.imshow(im)


# whole=[8,205,46,8,2,105,17,97,282,2,18,109,233,89,210,23,31]
# jrc=[79,436,234,231,19,171,329,706,1959,60,427,450,996,104,230,343,106]

# whole=[0,2,0,8,0,1,10,18,124,1,3,48,80,8,6,5,8]
# rd_sl_rrp=[0,1,0,3,0,0,6,12,88,1,2,17,35,0,0,5,4]
# rd_sl_rrp_annex_EN=[0,1,0,5,0,1,4,6,36,0,1,31,45,8,6,0,4]

#####Barplot#####

#Create mock data for barplot
# Data to be plotted
Rrp = [random.randint(0, 400) for i in range(1,18,1)]
RecPlan = [random.randint(0, 400) for i in range(1,18,1)]
EUSem = [random.randint(0, 400) for i in range(1,18,1)]

data=[Rrp,RecPlan,EUSem]

# Importing the matplotlib library
# Declaring the figure or the plot (y, x) or (width, height)
plt.figure(figsize=[15, 10])
# # Using numpy to group 3 different data with bars
X = np.arange(len(Rrp))
# # Passing the parameters to the bar function, this is the main function which creates the bar plot
# # Using X now to align the bars side by side
for count, array in enumerate(data):
    offset=1/len(data)
    plt.bar(X + count*offset, array, color = sdg_colors.values(), alpha = 1-count*offset/1.75, width = offset)    
    # plt.bar(X + 0.5, RecPlan, color = sdg_colors.values(), alpha = 0.95, width = 0.5)
    # plt.bar(X + 0.75, EUSem, color = sdg_colors.values(), alpha = 0.75, width = 0.5)
# Creating the legend of the bars in the plot
plt.legend(['maindoc+annex', 'rd_sl_rrp', 'rd_sl_rrp_annex'])
# Overiding the x axis with the country names
plt.xticks([i for i in range(0,17,1)], sdg_names, fontsize='large', fontweight='bold', rotation=45)
plt.yticks(fontsize='large', fontweight='bold')
# Giving the tilte for the plot
plt.title("Mentions", fontsize='large', fontweight='bold') #within {path.name}
# Namimg the x and y axis
#plt.xlabel('Countries')
plt.ylabel('Counts',fontsize='large', fontweight='bold')
plt.savefig('Barplot.png', dpi=300)
# Saving the plot as a 'png'
# if save_plot=True:
#     plt.savefig(svg_filepath_variable)
# Displaying the bar plot
plt.show()