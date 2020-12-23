# Set right working directory: Go to Session -> Set Working Directory -> To Source File Location
filename = "recovery_plan.R"
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

####read in new results
####make sure to set correct file directory for reading in data from pythin script
dat_2 <- read_excel("D:/Work_JRC/Mapping_2/results/processed/compare_results_recoveryplan.xlsx",sheet = "keyword_counts_RAW", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))
dat <- read_excel("D:/Work_JRC/Mapping_2/results/processed/compare_results_recoveryplan.xlsx",sheet = "aggregated_to_target_level", col_types = "list") %>%
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

percentiles <- quantile(unique(dat$txt_len), probs = c(0.01,0.05,0.5,0.95, 0.99))


#create empty vector and append index values where criteria does not apply
#drop rows based on index values from vector
vector = c()
j = 1
for(i in 1:length(dat$Policy)){
  #first percentile, take everything, no condition needed
  #< 1% percentile, take everything
  if(dat$txt_len[i]<percentiles[1]) {
    vector[j] <- i
    j = j + 1
  }
  #1 - 5% percentile, at least count==2 
  if(dat$txt_len[i]>percentiles[1] & dat$txt_len[i]<percentiles[2]) {
    if(dat$aggr_Count[i] > 1){
      vector[j] <- i
      j = j + 1
    }
    #5 - 95% percentile, count >= 3 OR 2 num keys >= 2
  } else if(dat$txt_len[i]>percentiles[2] & dat$txt_len[i]<percentiles[4]){
      if(dat$aggr_Count[i] >= 3 || dat$num_keys[i] > 2) {
        vector[j] <- i
        j = j + 1
      }
    #95 - 99% percentile, count => 4 OR num_keys >= 3
  } else if(dat$txt_len[i]>percentiles[4] & dat$txt_len[i]<percentiles[5]){
      if(dat$aggr_Count[i] >= 4 || dat$num_keys[i] > 3) {
        vector[j] <- i
        j = j + 1
      }
    #99% percentile, count >= 5 OR num_keys >= 3
  } else if(dat$txt_len[i]>percentiles[5]){
      if(dat$aggr_Count[i] >= 5 || dat$num_keys[i] > 3) {
        vector[j] <- i
        j = j + 1
      }
    } 
}



final_dat <- dat



#update n_targets
for (i in (1:length(pol_ls$`unique(dat$Policy)`))){
  temp_df <- final_dat[final_dat$Policy == pol_ls$`unique(dat$Policy)`[i], ]
  pol_ls$n_targets[i] <- length(temp_df$Policy)
}

final_dat$n_targets <- pol_ls$n_targets[match(final_dat$Policy, pol_ls$`unique(dat$Policy)`)]


#overview about target distribution
targets <- read.xlsx('Matrix_Basestructure.xlsx', sheetName = "Basis", header = FALSE)
targets <- data.frame(targets)
targets <- targets[1,2:length(targets)]
targets <- (base::lapply(targets, base::as.character))
targets <- data.frame(targets)
targets <- t(targets)
targets <- data.frame(targets)


target_overview <- as.data.frame(table(unlist(final_dat$Target)))
target_overview$Var1 <- as.character(target_overview$Var1)

nodataavailable <- as.data.frame(targets$targets[!(targets$targets %in% target_overview$Var1)])


#read in goal_target_list table
goals <- read.xlsx('goal_target_list.xlsx', sheetName = "Sheet1", header = TRUE)

#add goal to target_overview
target_overview$Goal <- 0
for (i in (1:length(target_overview$Var1))) {
  target_overview$Goal[i] <- as.character(goals$Goal[which(goals$Target == target_overview$Var1[i])])
}


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
csvtable <- read.csv('Matrix_Basestructure.csv', header = FALSE)

collabels <- csvtable[1,2:length(csvtable)]

collabels <- (base::lapply(collabels, base::as.character))

rowlabels <- csvtable[2:nrow(csvtable),1]

rowlabels <- (base::lapply(rowlabels, base::as.character))

data <- matrix(data=NA, nrow = length(rowlabels), ncol = length(collabels))

data <- data.frame(data)

colnames(data) <- collabels

rownames(data) <- rowlabels

data[is.na(data)] <- 0  ## replace NA in data by 0 

# add '_' in order to make string detect work in the loop
matrixcolnames <- data.matrix(collabels)

matrixcolnames[1:length(matrixcolnames),1] <- sub("^", "_", matrixcolnames[1:length(matrixcolnames),1])

matrixrownames <- data.matrix(rowlabels)

matrixrownames[1:length(matrixrownames),1] <- sub("^", "_", matrixrownames[1:length(matrixrownames),1])


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

#get number of policies per Goal and its percentage of all policies



pol_per_goal <- as.data.frame(unique(goals$Goal))
colnames(pol_per_goal) <- "SDG"
pol_per_goal$n_pol <- 0
for (i in (1:17)){
  temp_df <-  final_dat[final_dat$Goal == pol_per_goal$SDG[i] ,]
  pol_per_goal$n_pol[i] <-  length(unique(temp_df$Policy)) 
}

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

#get undetected policies 
pol_folder <- read_excel("folder_list.xlsx", sheet = "Policy_Names")
pol_folder <- pol_folder[,-1]
policies$Policies <- as.character(policies$Policies)
pol_2 <- as.data.frame(policies$Policies)
undet_pols <- pol_folder[!pol_folder$`0` %in% policies$Policies,]

undet_pols$txt_len <- dat_txtlen$Textlength[match(undet_pols$`0`, dat_txtlen$Policy)]

goal_overview <- as.data.frame(table(unlist(final_dat$Goal)))
goal_overview$id <- goal_ls$id[match(goal_overview$Var1, goal_ls$`SDGcol$Goal`)]
goal_overview <- goal_overview[order(goal_overview$id),]

##########    EXPORT    #########

#distribution of goals
write.xlsx(as.data.frame(goal_overview), file="results/processed/all_results_recoveryplan.xlsx", sheetName="goal_distribution", append =TRUE)
#write all in 1 excel workbook, except sankey data
#all keyword counts
write.xlsx(as.data.frame(dat_txtlen), file="results/processed/all_results_recoveryplan.xlsx", sheetName="raw_keywords", append =TRUE)
#aggregated to target-level without weighting rile
write.xlsx(as.data.frame(dat), file="results/processed/all_results_recoveryplan.xlsx", sheetName="aggregated_to_target_level", append =TRUE)
#aggrgated to target-level with weight applied
#write.xlsx(as.data.frame(final_dat), file="results/processed/all_results_recoveryplan.xlsx", sheetName="weight_applied", append =TRUE)
#undetecged targets
write.xlsx(as.data.frame(nodataavailable), file="results/processed/all_results_recoveryplan.xlsx", sheetName="undetected_targets", append =TRUE)
