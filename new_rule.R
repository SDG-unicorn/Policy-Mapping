# Set right working directory: Go to Session -> Set Working Directory -> To Source File Location
filename = "new_rule.R"
filepath = file.choose()  # browse and select your_file.R in the window
dir = substr(filepath, 1, nchar(filepath)-nchar(filename))
setwd(dir)

rm(list = ls(all=TRUE)) ##clears everything before script is run

library(XLConnect)
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

###################################
#############################################
######################################################
################################################################
####run this code block only if you want to merge old policies and new vdl initiatives
####make sure to set correct file directory for reading in data from pythin script
dat <- read_excel("results/raw/mapping_VdL_17112020.xlsx",sheet = "RAW", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))  

dat_dev_countr <- read_excel("results/raw/mapping_VdL_17112020.xlsx",sheet = "RAW_dev_countries", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))  
dat <- rbind(dat, dat_dev_countr)


###read in VdL results and merge
dat2 <- read_excel("results/raw/mapping_VdL_26102020.xlsx",sheet = "RAW", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))  

dat2_dev_countr <- read_excel("results/raw/mapping_VdL_26102020.xlsx",sheet = "RAW_dev_countries", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))  

dat2 <- rbind(dat2, dat2_dev_countr)

###############################################

#####merge pre vdl and vdl policies
#dat <- rbind(dat, dat2)
#drop first column
dat <- dat[,-1]

###############################################


#add column that counts keys per policy per target
dat_count <- as.data.frame(summarise(group_by(dat,Policy,Target),count =n()))
#aggregate keys to target level 
dat2 <- dat %>%
  group_by(Policy, Target) %>%
  summarise(aggr_Count=sum(as.numeric(Count)))
#column from dat_count to dat2
dat2$num_keys <- dat_count$count
dat2$txt_len <- dat$Textlength[match(dat2$Policy, dat$Policy)]

pol_ls <- unique(dat2$Policy)
n_targets <- as.data.frame(unique(dat2$Policy))
n_targets$n_targets <- 0
for(i in (1:length(pol_ls))){
  temp_df <- dat2[dat2$Policy == pol_ls[[i]],]  
  n_targets$n_targets[i] <- length(temp_df$Policy)
}
dat2$n_targets <- n_targets$n_targets[match(dat2$Policy, n_targets$`unique(dat2$Policy)`)]


####################################################################################
#############################################################
####################################################
################################




################################
#####################################################
#############################################################
####################################################################
####read in new results
####make sure to set correct file directory for reading in data from pythin script
dat_txtlen <- read_excel("D:/Work_JRC/Mapping_2/results/processed/VdL_17112020.xlsx",sheet = "keyword_counts_RAW", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))
dat <- read_excel("D:/Work_JRC/Mapping_2/results/processed/VdL_17112020.xlsx",sheet = "aggregated_to_target_level", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))
#make textlength numeric
dat_txtlen$Textlength <- as.numeric(dat_txtlen$Textlength)
dat$aggr_Count <- as.numeric(dat$aggr_Count)
#drop first column
dat <- dat[,-1]


#export list of policies for missing_policies.py script as input
pol_ls <- as.data.frame(unique(dat_txtlen$Policy))
# write.xlsx(pol_ls, "detected_pol.xlsx", sheetName = "list")

#add txtlen to dat
dat$txt_len <- dat_txtlen$Textlength[match(dat$Policy, dat_txtlen$Policy)]


#add number of detected targets to new column
#create list of unique policy names
pol_ls <- as.data.frame(unique(dat$Policy))
pol_ls$n_targets <- 0
for (i in (1:length(pol_ls$`unique(dat$Policy)`))){
  temp_df <- dat[dat$Policy == pol_ls$`unique(dat$Policy)`[i], ]
  pol_ls$n_targets[i] <- length(temp_df$Policy)
}

dat$n_targets <- pol_ls$n_targets[match(dat$Policy, pol_ls$`unique(dat$Policy)`)]

#add column that counts keys per policy per target
#dat_count <- as.data.frame(summarise(group_by(dat,Policy,Target),count =n()))

percentiles <- quantile(unique(dat$txt_len), probs = c(0.15,0.5,0.95,0.99))

#create empty vector and append index values where criteria does not apply
#drop rows based on index values from vector
vector = c()
j = 1
for(i in 1:length(dat$Policy)){
  #first percentile, take everything, no condition needed
  #< 5% percentile, take everything
  if(dat$txt_len[i]<percentiles[1]) {
    vector[j] <- i
    j = j + 1
  }
  #5 - 50% percentile, at least count==2 
  if(dat$txt_len[i]>percentiles[1] & dat$txt_len[i]<percentiles[2]) {
    if(dat$aggr_Count[i] > 1){
      vector[j] <- i
      j = j + 1
    }
    #50 - 95% percentile, count >= 3 OR 2 num keys >= 2
  } else if(dat$txt_len[i]>percentiles[2] & dat$txt_len[i]<percentiles[3]){
      if(dat$aggr_Count[i] >= 3 || dat$num_keys[i] > 2) {
        vector[j] <- i
        j = j + 1
      }

    #95% percentile, count >= 4 OR num_keys >= 3
  } else if(dat$txt_len[i]>percentiles[3]){
      if(dat$aggr_Count[i] >= 4 || dat$num_keys[i] > 3) {
        vector[j] <- i
        j = j + 1
      }
    } 
}


final_dat <- dat[vector,]

length(unique(final_dat$Policy))


#update n_targets
for (i in (1:length(pol_ls$`unique(dat$Policy)`))){
  temp_df <- final_dat[final_dat$Policy == pol_ls$`unique(dat$Policy)`[i], ]
  pol_ls$n_targets[i] <- length(temp_df$Policy)
}

final_dat$n_targets <- pol_ls$n_targets[match(final_dat$Policy, pol_ls$`unique(dat$Policy)`)]




#####################
#########################
#############################
################################
####dat_txt = raw keywords, dat = target-level, final_dat = weight applied
# dat_txtlen <- read_excel("D:/Work_JRC/Mapping_2/results/processed/Old_Policies/26102020_without_VdL_policies.xlsx",sheet = "raw_keywords", col_types = "list") %>%
#   dplyr::mutate_all(funs(as.character(.)))
# dat <- read_excel("D:/Work_JRC/Mapping_2/results/processed/Old_Policies/26102020_without_VdL_policies.xlsx",sheet = "aggregated_to_target_level", col_types = "list") %>%
#   dplyr::mutate_all(funs(as.character(.)))
# final_dat <- read_excel("D:/Work_JRC/Mapping_2/results/processed/Old_Policies/26102020_without_VdL_policies.xlsx",sheet = "weight_applied", col_types = "list") %>%
#   dplyr::mutate_all(funs(as.character(.)))
# 




#overview about target distribution
#read in goal_target_list table
goals <- read_excel('goal_target_list.xlsx', sheet = "Sheet1", col_names = TRUE)
targets <- as.data.frame(goals$Target)
colnames(targets) <- c("targets")
target_overview <- as.data.frame(table(unlist(final_dat$Target)))
target_overview$Var1 <- as.character(target_overview$Var1)

nodataavailable <- as.data.frame(targets$targets[!(targets$targets %in% target_overview$Var1)])


#add goal to target_overview
target_overview$Goal <- 0
for (i in (1:length(target_overview$Var1))) {
  target_overview$Goal[i] <- as.character(goals$Goal[which(goals$Target == target_overview$Var1[i])])
}


####################################################
#for EU RECOVERY PLAN
# dat$goal <- 0
# for (i in (1:length(dat$Policy))) {
#   dat$goal[i] <- as.character(goals$Goal[which(goals$Target == dat$Target[i])])
# }
# 
# ###how do results change when count = 1 is dropped?
# dat2 <- dat[dat$aggr_Count > 1,]
# 
# 
# goal_overview <- as.data.frame(aggregate(dat$aggr_Count, by=list(Category=dat$goal), FUN=sum))
# goal_to_add <- read_excel('D:/Work_JRC/Mapping_2/results/raw/mapping_goal_level_EU_Rec_26062020.xlsx', sheet = "RAW", col_names = TRUE)
# goal_to_add <- as.data.frame(aggregate(goal_to_add$Count, by=list(Category=goal_to_add$Goal), FUN=sum))
# goal_overview <- rbind(goal_overview, goal_to_add)
# goal_overview$Category <- stri_replace_all_fixed(goal_overview$Category, "SDG", "Goal")
# goal_overview <- as.data.frame(aggregate(goal_overview$x, by=list(Category=goal_overview$Category), FUN=sum))
# 
# ####export 
# #all keyword counts
# #drop last column 
# dat_txtlen <- dat_txtlen[,-6]
# xlcFreeMemory()
# write.xlsx(as.data.frame(dat_txtlen), file="results/processed/EU_Recovery_Plan_Results_26062020.xlsx", sheetName="raw_keywords", append =TRUE)
# 
#aggregated to target-level without weighting rile
# xlcFreeMemory()
# dat <- dat[, -5]
# dat <- dat[, -5]
# dat$percentage <- dat$aggr_Count / sum(dat$aggr_Count) * 100
# write.xlsx(as.data.frame(dat), file="results/processed/EU_Recovery_Plan_Results_26062020.xlsx", sheetName="aggregated_to_target_level", append =TRUE)
# 
# #goal_overview
# write.xlsx(as.data.frame(goal_overview), file="results/processed/EU_Recovery_Plan_Results_26062020.xlsx", sheetName="goal_level", append =TRUE)
# 
# #only targets with count greater 1 
# dat2$percentage <- dat2$aggr_Count / sum(dat2$aggr_Count) * 100
# write.xlsx(as.data.frame(dat2), file="results/processed/EU_Recovery_Plan_Results_26062020.xlsx", sheetName="targets_count_greater1", append =TRUE)
# 
#####################################################

final_dat$Goal <- target_overview$Goal[match(final_dat$Target, target_overview$Var1)]

goal_stats <- as.data.frame(table(unlist(final_dat$Goal)))


length(final_dat$Policy)
policies <- as.data.frame(unique(final_dat$Policy))
colnames(policies) <- "Policies"

policies$target_n <- 0
policies$goal_n <- 0
for (i in (1:length(policies$Policies))) {
  temp_df <-  final_dat[final_dat$Policy == policies$Policies[i] ,]
  policies$target_n[i] <- length(unique(temp_df$Target))
  policies$goal_n[i] <- length(unique(temp_df$Goal))
}

#sort descending
policies <- policies[with(policies, order(goal_n, decreasing = TRUE)), ]



##for the third visualization - sankey chart
policies$which_goals <- 0
policies$which_targets <- 0

for (i in (1:length(policies$Policies))) {
  temp_df <-  final_dat[final_dat$Policy == policies$Policies[i] ,]
  merged_string_targets <- ""
  for (j in (1:length(temp_df$Policy))) {
    print(temp_df$Target[j])
    merged_string_targets <- paste(merged_string_targets, temp_df$Target[j], sep = "_")
    policies$which_targets[i] <- merged_string_targets
  }
}

##create blank matrix with the desired extent and the correct row and column names

csvtable <- read_excel('Matrix_Basestructure.xlsx', sheet = "Basis")

collabels <- as.data.frame(csvtable[,1])

rowlabels <- collabels

data <- matrix(data=NA, nrow = length(rowlabels$...1), ncol = length(collabels$...1))

data <- data.frame(data)

colnames(data) <- collabels$...1

rownames(data) <- rowlabels$...1

data[is.na(data)] <- 0  ## replace NA in data by 0 

# add '_' in order to make string detect work in the loop
matrixcolnames <- collabels

matrixcolnames <- as.data.frame(gsub("^", "_", matrixcolnames$...1))
colnames(matrixcolnames) <- "Target"
matrixrownames <- matrixcolnames



sankey_output <- data.frame("tar_1" = NA, "tar_2" = NA, "number_policies" = NA, "Policies" = NA)
for (k in (1:length(policies$which_targets))) {
  # over policies
  for (i in (1:length(matrixcolnames$Target))) {
    # over columns, try for specific column in matrix
    if (stringi::stri_detect_fixed(policies$which_targets[k], matrixcolnames[i,])) {
      for (j in (1:length(matrixrownames$Target))) {
        # over rows, try for specific row in matrix and check outcome with Excel table where Im entirely sure about the value
        if (stringi::stri_detect_fixed((policies$which_targets[k]), matrixrownames[j,])) {
          temp_line <- data.frame("tar_1" = matrixcolnames[i,],"tar_2" =  matrixrownames[j,],"number_policies" =  1,"Policies" = policies$Policies[k])
          colnames(temp_line) <- c("tar_1", "tar_2", "number_policies", "Policies")
          sankey_output <-rbind(sankey_output, temp_line)
        } else { data[i,j] <- data[i,j]
        }
      }
    } else { data[i,j] <- data[i,j]
    }
  }
}


sankey_policies <- subset(sankey_output, select = c("tar_1", "tar_2", "Policies"))
sankey_n_pol <-  subset(sankey_output, select = c("tar_1", "tar_2", "number_policies"))

sankey_policies <-aggregate(data=sankey_policies,Policies~tar_1+tar_2,FUN=paste, collapse = " ; ")
sankey_n_pol <- aggregate(data=sankey_n_pol,number_policies~tar_1+tar_2,FUN=sum)

sankey_results <- merge(sankey_n_pol, sankey_policies, by=c("tar_1","tar_2"))

sankey_results$tar_1 <- gsub("_", "", sankey_results$tar_1)
sankey_results$tar_2 <- gsub("_", "", sankey_results$tar_2)

#flag rows whith same targets (e.g. from 1.1 to 1.1)
for (i in (1:length(sankey_results$tar_1))) {
  if(sankey_results$tar_1[i] == sankey_results$tar_2[i]) {
    sankey_results$number_policies[i] <- 1
  }
}

#drop rows where number_policies == 1
sankey_results <- sankey_results[!sankey_results$number_policies == 1,]

#add goal columns for labelling sankey diagram and drop down selection menu
#add goal color as well
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


sankey_results$Goal_tar_1 <- NA
sankey_results$Goal_tar_2 <- NA
sankey_results$tar_1_color <- NA
sankey_results$tar_2_color <- NA
for (i in (1:length(sankey_results$tar_1))) {
  sankey_results$Goal_tar_1[i] <- as.character(goals$Goal[which(goals$Target == sankey_results$tar_1[i])])
  sankey_results$Goal_tar_2[i] <- as.character(goals$Goal[which(goals$Target == sankey_results$tar_2[i])])
  sankey_results$tar_1_color[i] <- as.character(SDGcol$hex[which(SDGcol$Goal == sankey_results$Goal_tar_1[i])])
  sankey_results$tar_2_color[i] <- as.character(SDGcol$hex[which(SDGcol$Goal == sankey_results$Goal_tar_2[i])])
}

sankey_results$Goal_1_ID <- 0
for(i in (1:length(SDGcol$Goal))){
  for(j in (1:length(sankey_results$tar_1))){
    if(sankey_results$Goal_tar_1[j] == SDGcol$Goal[i]){
      sankey_results$Goal_1_ID[j] <- i
    }
  }
}

sankey_results$Goal_2_ID <- 0
for(i in (1:length(SDGcol$Goal))){
  for(j in (1:length(sankey_results$tar_1))){
    if(sankey_results$Goal_tar_2[j] == SDGcol$Goal[i]){
      sankey_results$Goal_2_ID[j] <- i
    }
  }
}

sankey_results$tar_1_ID <- 0
sankey_results$tar_2_ID <- 0

for (i in (1:length(sankey_results$tar_1))){
  for(j in (1:length(goals$Target))){
    if(sankey_results$tar_1[i] == goals$Target[j]){
      sankey_results$tar_1_ID[i] <- goals$Target_ID[j]
    }
    if(sankey_results$tar_2[i] == goals$Target[j]){
      sankey_results$tar_2_ID[i] <- goals$Target_ID[j]
    }
  }
}

sankey_results <- sankey_results %>% group_by(tar_1_ID) 
sankey_results <- sankey_results %>% arrange(tar_2_ID, .by_group = T)



#add percentage
pol_per_goal$percentage <- pol_per_goal$n_pol / sum(pol_per_goal$n_pol)*100

#identify policies with only 1 link
pol_1_target <- NULL
for (i in (1:length(policies$Policies))) {
  temp_df <-  final_dat[final_dat$Policy == policies$Policies[i] ,]
  if(length(temp_df$Policy) == 1) {
    pol_1_target <- c(pol_1_target, temp_df$Policy[1])  
  }
}

pol_1_target <- as.data.frame(pol_1_target)

#get all data of policy
pol_1target_only <- data.frame(Policy= NA, Target= NA, aggr_Count = NA, num_keys = NA, Textlength = NA, Goal = NA)
for (i in (1:length(pol_1_target$pol_1_target))){
  pol_1target_only[nrow(pol_1target_only)+1, ] <- final_dat[final_dat$Policy == pol_1_target$pol_1_target[i] ,]
}
pol_1target_only <- na.omit(pol_1target_only)



#order keyword count before exporting
dat_txtlen <- dat_txtlen[order(dat_txtlen$Policy),]

#add index to order target_overview properly, take goal list from sdgcol
goal_ls <- as.data.frame(SDGcol$Goal)
goal_ls$id <- seq(1,17)
#add id to goals df
goals$goal_id <- goal_ls$id[match(goals$Goal, goal_ls$`SDGcol$Goal`)]

target_overview$goal_id <- goals$goal_id[match(target_overview$Goal, goals$Goal)]
target_overview$tar_id <- goals$Target_ID[match(target_overview$Var1, goals$Target)]
target_overview <- target_overview[order(target_overview$tar_id),]
target_overview <- target_overview[,-4]
target_overview <- target_overview[,-4]

#get number of policies per Goal and its percentage of all policies
target_overview$cat_1 <- 0
target_overview$cat_2 <- 0
# target_overview$cat_3 <- 0
target_overview$checkup <- 0
for (i in (1:length(target_overview$Var1))){
  temp_df <-  final_dat[final_dat$Target == target_overview$Var1[i] ,]
  print(temp_df$Category)
  target_overview$checkup[i] <- nrow(temp_df)
  target_overview$cat_1[i] <- nrow(temp_df[temp_df$Category == "1",])
  target_overview$cat_2[i] <- nrow(temp_df[temp_df$Category == "2",])
#  target_overview$cat_3[i] <- nrow(temp_df[temp_df$Category == "3",])
}





#get undetected policies 

###use this for old policies mapping
# pol_folder <- read_excel("folder_list.xlsx", sheet = "Policy_Names")
# pol_folder <- pol_folder[,-1]
# policies$Policies <- as.character(policies$Policies)
# pol_2 <- as.data.frame(policies$Policies)
# undet_pols <- pol_folder[!pol_folder$Policy %in% policies$Policies,]
# undet_pols$txt_len <- dat_txtlen$Textlength[match(undet_pols$Policy, dat_txtlen$Policy)]
# colnames(undet_pols) <- c('Policy', 'Txtlen')
#############

####use this for vdl policies
pol_folder <- read.csv("D:/Work_JRC/Mapping_2/Query/2020-10-07_vdl_query_subset.csv", header=TRUE)
policies$Policies <- as.character(policies$Policies)
pol_2 <- as.data.frame(policies$Policies)
undet_pols <- pol_folder[!pol_folder$celex_codes %in% policies$Policies,]
undet_pols <- as.data.frame(undet_pols$celex_codes)
colnames(undet_pols) <- 'Policy'
undet_pols$txt_len <- dat_txtlen$Textlength[match(undet_pols$Policy, dat_txtlen$Policy)]
colnames(undet_pols) <- c('Policy', 'Txtlen')


############# check whether any keywords where detected and add to results


append_df <- data.frame(data.frame(matrix(ncol = 6, nrow = 0)))
colnames(append_df) <- colnames(dat_txtlen)
for(i in 1:length(undet_pols$Policy)){
  temp_df <- dat_txtlen[dat_txtlen$Policy == undet_pols$Policy[i],]
  append_df <- rbind(append_df, temp_df)  
}


##############################################################################

##########    EXPORT    #########
goals$goal_id <- goal_ls$id[match(goals$Goal, goal_ls$`SDGcol$Goal`)]

goal_overview <- as.data.frame(table(unlist(final_dat$Goal)))

options(java.parameters = "-Xmx4g")

#clean some memory space for exporting everything
xlcFreeMemory()


##############before exporting add policy category to each df

#read in categories for old policies
# categories <- read_excel("policies_categories_final.xlsx", sheet = "folder_list")

#read in categories for new policies
categories <- read_excel("D:/Work_JRC/Mapping_2/Query/titles_codes_categories.xlsx", sheet = "folder_list")
#rename columns to make the match work
colnames(categories) <- c('index','title','Policy','Hyperlink', 'Category')



#add categories to df's
dat_txtlen$Category <- categories$Category[match(dat_txtlen$Policy, categories$Policy)]
dat$Category <- categories$Category[match(dat$Policy, categories$Policy)]
final_dat$Category <- categories$Category[match(final_dat$Policy, categories$Policy)]
policies$Category <- categories$Category[match(policies$Policies, categories$Policy)]
undet_pols$Category <- categories$Category[match(undet_pols$Policy, categories$Policy)]
pol_1target_only$Category <- categories$Category[match(pol_1target_only$Policy, categories$Policy)]
# append_df$Category <- categories$Category[match(append_df$Policy, categories$Policy)]

#get number of policies per Goal and its percentage of all policies
target_overview$cat_1 <- 0
target_overview$cat_2 <- 0
# target_overview$cat_3 <- 0
target_overview$checkup <- 0
for (i in (1:length(target_overview$Var1))){
  temp_df <-  final_dat[final_dat$Target == target_overview$Var1[i] ,]
  print(temp_df$Category)
  target_overview$checkup[i] <- nrow(temp_df)
  target_overview$cat_1[i] <- nrow(temp_df[temp_df$Category == "1",])
  target_overview$cat_2[i] <- nrow(temp_df[temp_df$Category == "2",])
  # target_overview$cat_3[i] <- nrow(temp_df[temp_df$Category == "3",])
}


#get number of policies per Goal and its percentage of all policies
pol_per_goal <- as.data.frame(unique(goals$Goal))
colnames(pol_per_goal) <- "SDG"
pol_per_goal$n_pol <- 0

unique_df <- final_dat[!duplicated(final_dat[,c(1,8)]),]
for (i in (1:17)){
  temp_df <-  unique_df[unique_df$Goal == pol_per_goal$SDG[i] ,]
  pol_per_goal$n_pol[i] <- nrow(temp_df)
  pol_per_goal$cat_1[i] <- nrow(temp_df[temp_df$Category == "1",])
  pol_per_goal$cat_2[i] <- nrow(temp_df[temp_df$Category == "2",])
  #pol_per_goal$cat_3[i] <- nrow(temp_df[temp_df$Category == "3",])
}



##add proper titles to New Policies Celex Codes
#first rename policy into celex column
colnames(dat_txtlen)[2] <- 'celex'
colnames(dat)[1] <- 'celex'
colnames(final_dat)[1] <- 'celex'
colnames(policies)[1] <- 'celex'
colnames(undet_pols)[1] <- 'celex'
colnames(pol_1target_only)[1] <- 'celex'
colnames(append_df)[2] <- 'celex'


dat_txtlen$Policy <- categories$title[match(dat_txtlen$celex, categories$Policy)]
dat$Policy <- categories$title[match(dat$celex, categories$Policy)]
final_dat$Policy <- categories$title[match(final_dat$celex, categories$Policy)]
policies$Policy <- categories$title[match(policies$celex, categories$Policy)]
undet_pols$Policy <- categories$title[match(undet_pols$celex, categories$Policy)]
pol_1target_only$Policy <- categories$title[match(pol_1target_only$celex, categories$Policy)]
append_df$Policy <- categories$title[match(append_df$celex, categories$Policy)]




#add celex code as last column again to have proper Identifier
# dat_txtlen$celex <- categories$Policy[match(dat_txtlen$Policy, categories$title)]
# dat$celex <- categories$Policy[match(dat$Policy, categories$title)]
# final_dat$celex <- categories$Policy[match(final_dat$Policy, categories$title)]
# policies$celex <- categories$Policy[match(policies$Policies, categories$title)]
# undet_pols$celex <- categories$Policy[match(undet_pols$Policy, categories$title)]
# pol_1target_only$celex <- categories$Policy[match(pol_1target_only$Policy, categories$title)]
# append_df$celex <- categories$Policy[match(append_df$Policy, categories$title)]



####DROP ALL POLICIES THAT ARE CATEGORY 3 BEFORE FINAL EXPORT########
##only applies for old policies
# dat_txtlen <- dat_txtlen[!dat_txtlen$Category=='3',]
# dat <- dat[!dat$Category=='3',]
# final_dat <- final_dat[!final_dat$Category=='3',]
# policies <- policies[!policies$Category=='3',]
# undet_pols <- undet_pols[!undet_pols$Category=='3',]
# pol_1target_only <- pol_1target_only[!pol_1target_only$Category=='3',]


##############################################


#write all in 1 excel workbook, except sankey data
#all keyword counts
write.xlsx(as.data.frame(dat_txtlen), file="results/processed/VdL_17122020_processed.xlsx", sheetName="raw_keywords", append =TRUE)
xlcFreeMemory()
#aggregated to target-level without weighting rile
write.xlsx(as.data.frame(dat), file="results/processed/VdL_17122020_processed.xlsx", sheetName="aggregated_to_target_level", append =TRUE)
xlcFreeMemory()

#aggrgated to target-level with weight applied
write.xlsx(as.data.frame(final_dat), file="results/processed/VdL_17122020_processed.xlsx", sheetName="weight_applied", append =TRUE)
xlcFreeMemory()

#export with other aggregation rule, other percentiles
#write.xlsx(as.data.frame(final_dat_2), file="results/processed/other_aggregation_rule_17062020.xlsx", sheetName="weight_applied")
#xlcFreeMemory()


#policies per goal
write.xlsx(as.data.frame(pol_per_goal), file="results/processed/VdL_17122020_processed.xlsx", sheetName="policies_per_goal", append =TRUE)
xlcFreeMemory()

#policies per target
write.xlsx(as.data.frame(target_overview), file="results/processed/VdL_17122020_processed.xlsx", sheetName="policies_per_target", append =TRUE)
xlcFreeMemory()

#undetecged targets
write.xlsx(as.data.frame(nodataavailable), file="results/processed/VdL_17122020_processed.xlsx", sheetName="undetected_targets", append =TRUE)
xlcFreeMemory()

#targets, goals per policy
#rename policies column for coherence
colnames(policies)[1] <- "Policy"
write.xlsx(as.data.frame(policies), file="results/processed/VdL_17122020_processed.xlsx", sheetName="targets_per_policy", append =TRUE)
xlcFreeMemory()

#policies without targets
write.xlsx(as.data.frame(undet_pols), file="results/processed/VdL_17122020_processed.xlsx", sheetName="policies_without_targets", append =TRUE)
xlcFreeMemory()

#write.xlsx(as.data.frame(undet_pols), file="results/processed/undetected_policies_recoveryplan.xlsx", sheetName="policies_without_targets", append =TRUE)

#policies where 1 target was detected only
#drop last column
pol_1target_only <- pol_1target_only[,-6]
write.xlsx(as.data.frame(pol_1target_only), file="results/processed/VdL_17122020_processed.xlsx", sheetName="policies_1_target_only", append =TRUE)
xlcFreeMemory()


#### policies for which no targets were detected according to the aggregation rule, but they had keywords
write.xlsx(as.data.frame(append_df), file="results/processed/policies_without_Targets_but_with_keywords_VdL_17122020_processed.xlsx", sheetName="targets", append =TRUE)
xlcFreeMemory()


#For bubbleplot
write.xlsx(pol_per_goal, file = "results/processed/bubbleplot/data_for_bubbleplot_VdL_17122020_processed.xlsx", sheetName = "Policies_per_Goal", append = T, row.names = F)
xlcFreeMemory()


target_overview <- target_overview[, 1:5]
write.xlsx(target_overview, file = "results/processed/bubbleplot/data_for_bubbleplot_VdL_17122020_processed.xlsx", sheetName = "Policies_per_Target", append = T, row.names = F)
xlcFreeMemory()


#for policy coherence
sankey_results <- subset(sankey_results, select = c("tar_1", "tar_2", "number_policies", "Policies", "Goal_tar_1", "Goal_tar_2"))

target_descriptions <- read.csv2(file = "SDG-targets.csv", header = T, sep = ",")

####add Goal description for target-SDG
SDG_description <- as.data.frame(SDGcol$Goal)
SDG_description$description <- c("No poverty", "Zero Hunger", "Good health and well-being", "Quality education",
                                 "Gender equality", "Clean water and sanitation", "Affordable and clean energy",
                                 "Decent work and economic growth", "Industry, innovation and infrastructure",
                                 "Reduced inequalities", "Sustainable cities and communities", "Responsible consumption and production",
                                 "Climate action", "Life below water", "Life on land", "Peace, justice and strong institutions",
                                 "Partnerships for the goals")

sankey_results$Sdg_description <- SDG_description$description[match(sankey_results$Goal_tar_2, SDG_description$`SDGcol$Goal`)]

####add target description for Source SDG target
sankey_results$Target_Description <- target_descriptions$description[match(sankey_results$tar_1, target_descriptions$target)]

###for Diego, write to csv
write.csv(sankey_results,"policy-coherence_VdL_17122020_processed.csv", row.names = FALSE)


#sankey_results$Goal <- sankey_results$Goal_tar_1
write.xlsx(as.data.frame(sankey_results), file="results/processed/policy_coherence_Old_Mapping_16122020_processed.xlsx", sheetName="overlapping_policies")

#export session info
#writeLines(capture.output(sessionInfo()), "sessionInfo.txt")

#########due to long titles export everything also as csv



