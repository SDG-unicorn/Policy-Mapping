# Set right working directory: Go to Session -> Set Working Directory -> To Source File Location
filename = "process_python_output.R"
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
library(svDialogs)
library(tcltk)


#get current date
current_date <- Sys.Date()


############################################
####read in new results
####make sure to set correct file directory for reading in data from pythin script


aggregate_to_target_level <- function(){
  select_file <- choose.files()
  dat_raw <- read_excel(select_file, sheet = "RAW", col_types = "list") %>%
    dplyr::mutate_all(funs(as.character(.)))
  dat_dev_countr_raw <- read_excel(select_file,sheet = "RAW_dev_countries", col_types = "list") %>%
    dplyr::mutate_all(funs(as.character(.)))  
  #merge both outputs
  dat_raw <- rbind(dat_raw, dat_dev_countr_raw)
  #drop first column
  dat_raw <- dat_raw[,-1]
  #add column that counts keys per policy per target
  dat_count <- as.data.frame(summarise(group_by(dat_raw,Policy,Target),count =n()), keywords = paste0(Keyword, collapse = " - "))
  dat_keys <- group_by(dat_raw, Policy, Target) %>%
    summarise(keywords = paste0(Keyword, collapse = " - "))
  #pol_ls <- as.data.frame(unique(dat_count$Policy))
  # write.xlsx(pol_ls, "detected_pol.xlsx", sheetName = "list")
  #aggregate keys to target level 
  dat_target_level <- dat_raw %>%
    group_by(Policy, Target) %>%
    summarise(aggr_Count=sum(as.numeric(Count)))
  #column from dat_count to dat_target_level
  dat_target_level$num_keys <- dat_count$count
  dat_target_level <- merge(dat_target_level, dat_keys)
  #create final ist with different df's to be returned from the function as you cannot return multiple objects in R
  return_dfs_list <- list("dat_raw" = dat_raw, "dat_target_level" = dat_target_level)
  return(return_dfs_list)
}

list_of_dfs <- aggregate_to_target_level()
dat_raw <- list_of_dfs$dat_raw
dat_target_level <- list_of_dfs$dat_target_level

###########################################
####################################
###########################
####################
##############



#############
###################
############################
####################################
######## FUNCTION TO FILTER THE RESULTS ###############
#############################################



filter_results <- function(df_raw, df_target){
  #make textlength numeric
  df_raw$Textlength <- as.numeric(df_raw$Textlength)
  df_target$aggr_Count <- as.numeric(df_target$aggr_Count)
  pol_ls <- as.data.frame(unique(df_target$Policy))
  export_policy_list <- askYesNo(msg = "Do you want to export the list of detected policies to Excel?", default = TRUE, 
                    prompts = getOption("askYesNo", gettext(c("Yes", "No", "Cancel"))))
  if (export_policy_list == TRUE){
    write.xlsx(pol_ls, paste("detected_pol_", current_date, ".xlsx", sep = ""), sheetName = "list") 
  }
  #add txtlen to dat
  df_target$txt_len <- df_raw$Textlength[match(df_target$Policy, df_raw$Policy)]
  #add number of detected targets to new column
  #create list of unique policy names
  pol_ls$n_targets <- 0
  for (i in (1:length(pol_ls$`unique(df_target$Policy)`))){
    temp_df <- df_target[df_target$Policy == pol_ls$`unique(df_target$Policy)`[i], ]
    pol_ls$n_targets[i] <- length(temp_df$Policy)
  }
  df_target$n_targets <- pol_ls$n_targets[match(df_target$Policy, pol_ls$`unique(df_target$Policy)`)]
  #add column that counts keys per policy per target
  #dat_count <- as.data.frame(summarise(group_by(dat,Policy,Target),count =n()))
  percentiles <- quantile(unique(df_target$txt_len), probs = c(0.15,0.5,0.95,0.99))
  #create empty vector and append index values where criteria does not apply
  #drop rows based on index values from vector
  vector = c()
  j = 1
  for(i in 1:length(df_target$Policy)){
    #first percentile, take everything, no condition needed
    #< 5% percentile, take everything
    if(df_target$txt_len[i]<percentiles[1]) {
      vector[j] <- i
      j = j + 1
    }
    #5 - 50% percentile, at least count==2 
    if(df_target$txt_len[i]>percentiles[1] & df_target$txt_len[i]<percentiles[2]) {
      if(df_target$aggr_Count[i] > 1){
        vector[j] <- i
        j = j + 1
      }
      #50 - 95% percentile, count >= 3 OR 2 num keys >= 2
    } else if(df_target$txt_len[i]>percentiles[2] & df_target$txt_len[i]<percentiles[3]){
      if(df_target$aggr_Count[i] >= 3 || df_target$num_keys[i] > 2) {
        vector[j] <- i
        j = j + 1
      }
      #95% percentile, count >= 4 OR num_keys >= 3
    } else if(df_target$txt_len[i]>percentiles[3]){
      if(df_target$aggr_Count[i] >= 4 || df_target$num_keys[i] > 3) {
        vector[j] <- i
        j = j + 1
      }
    } 
  }
  final_dat <- df_target[vector,]
  length(unique(final_dat$Policy))
  #update n_targets
  for (i in (1:length(pol_ls$`unique(df_target$Policy)`))){
    temp_df <- final_dat[final_dat$Policy == pol_ls$`unique(df_target$Policy)`[i], ]
    pol_ls$n_targets[i] <- length(temp_df$Policy)
  }
  final_dat$n_targets <- pol_ls$n_targets[match(final_dat$Policy, pol_ls$`unique(df_target_$Policy)`)]
  return(final_dat)
}



filtered_dat <- filter_results(dat_raw, dat_target_level)


####################################
###########################
###################
#############
######


################
########################
###################################
#############################################
######### overview about target distribution ##############

get_target_distribution <- function(final_dat){
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
  
  
  
}

