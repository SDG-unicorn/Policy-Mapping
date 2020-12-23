# Set right working directory: Go to Session -> Set Working Directory -> To Source File Location
filename = "add_policies_ID.R"
filepath = file.choose()  # browse and select your_file.R in the window
dir = substr(filepath, 1, nchar(filepath)-nchar(filename))
setwd(dir)

rm(list = ls(all=TRUE)) ##clears everything before script is run


library(flextable)
library(reportr)
library(officer)
library(readxl) 
library(data.table) 
library(dplyr)
library(expss)
library(stringi)
library(xlsx)
library(splitstackshape)
library(matrixStats)
library(tidyr)
library(knitr)
library(kableExtra)
library(sqldf)
library(ggplot2)
library(scales)
library(stringr)


### read in new data results
all_dat <- read_excel("D:/Work_JRC/Mapping_2/results/processed/Vdl_Mapping_17112020_processed.xlsx",sheet = "weight_applied", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))

length(unique(all_dat$celex))

all_dat <- final_dat

all_dat$aggr_Count <- as.numeric(all_dat$aggr_Count)

all_dat <- all_dat %>% 
  group_by(celex, Target) %>% 
  summarise(aggr_Count = sum(aggr_Count))

#read in goal_target_list table
goals <- read_excel('goal_target_list.xlsx', sheet = "Sheet1", col_names = TRUE)

#add goal to target_overview
all_dat$Goal <- 0
for (i in (1:length(all_dat$celex))) {
  all_dat$Goal[i] <- as.character(goals$Goal[which(goals$Target == all_dat$Target[i])])
}

pol_ls <- as.data.frame(unique(all_dat$celex))
pol_ls$ID <- seq(0, length(pol_ls$`unique(all_dat$celex)`)-1)

all_dat$ID <- 0
for(i in (1:length(all_dat$celex))) {
  for(j in (1:length(pol_ls$`unique(all_dat$celex)`))) {  
    if(all_dat$celex[i] == pol_ls$`unique(all_dat$celex)`[j]) {
      all_dat$ID[i] <- pol_ls$ID[j]  
    }
  }
}

SDGcol <- c(rgb(237,27,42, maxColorValue = 255), rgb(217,169,51, maxColorValue = 255), rgb(35,157,74, maxColorValue = 255), 
            rgb(201,31,53, maxColorValue = 255), rgb(239,65,41, maxColorValue = 255), rgb(1,174,217, maxColorValue = 255), 
            rgb(252,183,20, maxColorValue = 255), rgb(141,25,58, maxColorValue = 255), rgb(249,106,39, maxColorValue = 255), 
            rgb(225,20,133, maxColorValue = 255), rgb(248,157,41, maxColorValue = 255), rgb(210,140,35, maxColorValue = 255), 
            rgb(71,119,61, maxColorValue = 255), rgb(1,124,191, maxColorValue = 255), rgb(61,176,75, maxColorValue = 255), 
            rgb(2,85,137, maxColorValue = 255), rgb(24,54,105, maxColorValue = 255))
SDGcol <- data.frame(SDGcol)
colnames(SDGcol) <- "hex"
SDGcol$Goal <- c("SDG 1", "SDG 2", "SDG 3", "SDG 4", "SDG 5", "SDG 6", "SDG 7", "SDG 8", "SDG 9", "SDG 10","SDG 11", "SDG 12",
                 "SDG 13", "SDG 14", "SDG 15", "SDG 16", "SDG 17")


all_dat$SDGcol <- 0
for(i in (1:length(all_dat$Goal))){
  for(j in (1:length(SDGcol$Goal))) {
    if(all_dat$Goal[i] == SDGcol$Goal[j]){
      all_dat$SDGcol[i] <- as.character(SDGcol$hex[j])
    }
  }
}

all_dat$tar_ID <- 0
for(i in (1:length(all_dat$Goal))){
  for(j in (1:length(goals$Target_ID))) {
    if(all_dat$Target[i] == goals$Target[j]){
      all_dat$tar_ID[i] <- goals$Target_ID[j]
    }
  }    
} 
   
all_dat <- all_dat %>% group_by(celex) %>% arrange(tar_ID)

all_dat <- all_dat %>% group_by(celex) %>% arrange(celex)



all_dat$celex <- as.character(all_dat$celex)
all_dat$Target <- as.character(all_dat$Target)
all_dat$aggr_Count <- as.numeric(all_dat$aggr_Count)
all_dat$Goal <- as.character(all_dat$Goal)
all_dat$ID <- as.numeric(all_dat$ID)
all_dat$SDGcol <- as.character(all_dat$SDGcol)
all_dat$tar_ID - as.numeric(all_dat$tar_ID)

#for new policies
categories <- read_excel("D:/Work_JRC/Mapping_2/Query/titles_codes_categories.xlsx", sheet = "folder_list")
colnames(categories) <- c('index','title','Policy','Hyperlink', 'Category')

#add proper titles to table
all_dat$Policy <- categories$title[match(all_dat$celex, categories$Policy)]


#for old policies
# categories <- read_excel("policies_categories_final.xlsx", sheet = "folder_list")


#add categories to df's
all_dat$Category <- categories$Category[match(all_dat$celex, categories$Policy)]

#add hyperlink
all_dat$Hyperlink <- categories$Hyperlink[match(all_dat$celex, categories$Policy)]

#check for na
na_dat = all_dat[is.na(all_dat$Category),]


# all_dat$celex_codes <- categories$Policy[match(all_dat$Policy, categories$title)]


#check for na and fix categories
nans <- subset(all_dat, is.na(all_dat$Category))
print(nans$Policy)

#### add target description
target_descriptions <- read.csv2(file = "SDG-targets.csv", header = T, sep = ",")

all_dat$Target_Description <- target_descriptions$description[match(all_dat$Target, target_descriptions$target)]


write.xlsx(as.data.frame(all_dat), "sankey_input_VdL_17122020.xlsx" , sheetName = "RAW")




############# ONLY FOR OLD POLICIES ##########
#read in policy list to add hyperlinks 

# hyper <- read_excel("D:/Work_JRC/Mapping_2/Diego/Old/Policy_list_right.xlsx",sheet = "for_Diego_1", col_types = "list") %>%
#   dplyr::mutate_all(funs(as.character(.)))
# 
# categories$Hyperlink <- 0
# for (i in (1:length(categories$Category))){
#   for (f in (1:length(hyper$Category_final))){
#     if(categories$Policy[i] == hyper$Name[j] || ifcategories$Policy[i] == hyper$NewNameSuggestions[j]){
#       categories$Hyperlink[i] <- hyper$LinkEuLex[j]
#     }
#   }
# }

      
###############





