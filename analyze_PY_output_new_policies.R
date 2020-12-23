# Set right working directory: Go to Session -> Set Working Directory -> To Source File Location
filename = "analyze_PY_output_new_policies.R"
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
dat <- read_excel("results/raw/mapping_old_16122020.xlsx",sheet = "RAW", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))  

dat_dev_countr <- read_excel("results/raw/mapping_old_16122020.xlsx",sheet = "RAW_dev_countries", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))  

dat <- rbind(dat, dat_dev_countr)

#drop first column
dat <- dat[,-1]


#add column that counts keys per policy per target
dat_count <- as.data.frame(summarise(group_by(dat,Policy,Target),count =n()), keywords = paste0(Keyword, collapse = " - "))

dat_keys <- group_by(dat, Policy, Target) %>%
  summarise(keywords = paste0(Keyword, collapse = " - "))


pol_ls <- as.data.frame(unique(dat_count$Policy))
# write.xlsx(pol_ls, "detected_pol.xlsx", sheetName = "list")


#aggregate keys to target level 
dat2 <- dat %>%
  group_by(Policy, Target) %>%
  summarise(aggr_Count=sum(as.numeric(Count)))

#column from dat_count to dat2
dat2$num_keys <- dat_count$count

###define which counts to drop
#drop now targets with a count > 2 or have at least 2 different keywords detected
dat3 <- dat2[(dat2$aggr_Count > 0 | dat2$num_keys > 0), ]

dat3 <- merge(dat3, dat_keys)

# new_res <- subset(dat3, select = c("Policy", "Target"))
# new_res$Target <- trimws(new_res$Target, which = c("both"))
# new_res <- data.frame(lapply(new_res, as.character), stringsAsFactors=FALSE)
#more than 1300 dropped

length(unique(dat3$Policy))

#keep only top n targets
# 
# dat4 <- dat3 %>%
#   group_by(Policy) %>%
#   top_n(n = 8, wt = aggr_Count)
# 
# dat4 <- dat4 %>%
#   arrange(Policy, desc(aggr_Count))
# 
# dat5 <- as.data.frame(table(unlist(dat$Policy)))
# dat6 <- as.data.frame(table(unlist(dat2$Policy)))
# 
# dat_weight <- merge(dat5, dat6, by = "Var1")
# colnames(dat_weight) <- c("Policy", "n_keys_raw", "n_targets")
# dat7 <- dat[!duplicated(dat[,'Policy']),]
# dat_weight <- merge(dat_weight, dat7, by = "Policy")
# dat_weight <- subset(dat_weight, select = c("Policy", "n_keys_raw", "n_targets", "Textlength"))
# 
# 
# # Simple Scatterplot
# #first make textlength numeric
# 
# #create df of txt length frequencies and see which ones to drop as they skew the plot
# txt_length <- as.data.frame(table(dat$Textlength))
# txt_length$Var1 <- as.character(txt_length$Var1)
# txt_length$Var1 <- as.numeric(txt_length$Var1)
# txt_length <- txt_length[order(txt_length$Var1),]
# 
# dat_weight$Textlength <- as.numeric(dat_weight$Textlength)
# 
# dat2$txt_len <- dat$Textlength[match(dat2$Policy, dat$Policy)]
# 
# pol_ls <- unique(dat2$Policy)
# 
# n_targets <- as.data.frame(unique(dat2$Policy))
# n_targets$n_targets <- 0
# for(i in (1:length(pol_ls))){
#   temp_df <- dat2[dat2$Policy == pol_ls[[i]],]  
#   n_targets$n_targets[i] <- length(temp_df$Policy)
# }
# #match with policy names in dat2
# dat2$n_targets <- n_targets$n_targets[match(dat2$Policy, n_targets$`unique(dat2$Policy)`)]
# 
# scatter <- subset(dat2, select = c("Policy", "txt_len", "n_targets"))
# scatter <- scatter[!duplicated(scatter),]
# scatter$txt_len <- as.numeric(scatter$txt_len)
# scatter <- scatter[order(scatter$txt_len),]
# 
# cor(scatter$txt_len, scatter$n_targets, method = "pearson")
# cor(scatter$txt_len, scatter$n_targets, method = "kendall")
# cor(scatter$txt_len, scatter$n_targets, method = "spearman")
# 
# 
# p1 <- ggplot(scatter, aes(x = reorder(Policy, txt_len), y =n_targets)) +
#   geom_point()
# p1
# 
# #plot textlengths and sort with textlength
# scatter_2 <- subset(dat7, select = c("Policy", "Textlength"))
# scatter_2$Textlength <- as.numeric(scatter_2$Textlength)
# scatter_2 <- scatter_2[order(scatter_2$Textlength),]
# 
# p2 <- ggplot(scatter_2, aes(x = reorder(Policy, Textlength), y = Textlength)) +
#   geom_point()
# p2 + scale_y_continuous(labels = comma)
# 
# #drop outliers and plot again
# scatter_3 <- scatter_2[scatter_2$Textlength < 1000000,]
# 
# p2 <- ggplot(scatter_3, aes(x = reorder(Policy, Textlength), y = Textlength)) +
#   geom_point()
# p2 + scale_y_continuous(labels = comma)
# 
# #plot frequencies
# 
# 
# 
# summary(dat_weight$Textlength)
# 
# target_summary <- as.data.frame(table(dat2$Target))
# mean(target_summary$Freq)

# dat_goal <- read_excel("results/raw/mapping_goal_level_TEI_DEVCO_16112020.xlsx",sheet = "RAW", col_types = "list") %>%
#   dplyr::mutate_all(funs(as.character(.)))  
# 
# #add sdg column to dat3
# goals <- read_excel('goal_target_list.xlsx', sheet = "Sheet1", col_names = TRUE)
# targets <- as.data.frame(goals$Target)
# colnames(targets) <- c("targets")
# 
# 
# dat3$Goal <- 0
# for (i in (1:length(dat3$Target))) {
#   dat3$Goal[i] <- as.character(goals$Goal[which(goals$Target == dat3$Target[i])])
# }
# 
# 
# dat_goal <- subset(dat_goal, select = c("Policy", "Goal", "Count"))
# to_add <- subset(dat3, select = c("Policy", "Target", "Goal", "aggr_Count"))
# #group to_add by goal and count
# groupColumns1 = c("Policy","Goal")
# dataColumns1 = "aggr_Count"
# res1 = ddply(to_add, groupColumns1, function(x) colSums(x[dataColumns1]))
# 
# 
# names(res1) <- c("Policy", "Goal", "Count")
# 
# goal_overview <- rbind(res1, dat_goal)
# goal_overview$Count <- as.numeric(goal_overview$Count)
# groupColumns = c("Policy","Goal")
# dataColumns = "Count"
# library(plyr)
# res = ddply(goal_overview, groupColumns, function(x) colSums(x[dataColumns]))






#write aggregated keys and old results to separate sheets
# make sure correct directory is set
write.xlsx(as.data.frame(dat), file="results/processed/mapping_old_16122020_processed.xlsx", sheetName="raw_keywords")
write.xlsx(as.data.frame(dat3), file="results/processed/mapping_old_16122020_processed.xlsx", sheetName="aggregated_to_target_level", append =TRUE)
#write.xlsx(as.data.frame(goal_overview), file="results/processed/TEI_16112020.xlsx", sheetName="aggregated_to_goal_level", append =TRUE)
#write.xlsx(as.data.frame(dat4), file="results/processed/compare_results_26052020.xlsx", sheetName="only_top8_targets_per_policy", append =TRUE)





