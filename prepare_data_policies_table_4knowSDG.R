# Set right working directory: Go to Session -> Set Working Directory -> To Source File Location
filename = "prepare_data_policies_table_4knowSDG.R"
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
all_dat <- read_excel("D:/Work_JRC/Mapping_2/sankey_input_VdL_17122020.xlsx",sheet = "RAW", col_types = "list") %>%
  dplyr::mutate_all(funs(as.character(.)))

pol_ls <- as.data.frame(unique(all_dat$celex))
colnames(pol_ls) <- "Policy"


output_df <- data.frame(matrix(ncol = 19, nrow = 0))
colnames(output_df) <- c("ID", "POLICY", "SDG 1", "SDG 2","SDG 3","SDG 4","SDG 5", 
                         "SDG 6", "SDG 7", "SDG 8", "SDG 9", "SDG 10","SDG 11",
                         "SDG 12","SDG 13","SDG 14","SDG 15", "SDG 16", "SDG 17")


for (i in (1:length(pol_ls$Policy))){
  temp_df <- all_dat[all_dat$celex == pol_ls$Policy[i], ]
  row_4_df <- as.data.frame(c(i,temp_df$celex[1],0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0))
  row_4_df <- as.data.frame(t(row_4_df))
  row_4_df <- data.frame(lapply(row_4_df, as.character), stringsAsFactors=FALSE)
  colnames(row_4_df) <- c("ID", "POLICY", "SDG 1", "SDG 2","SDG 3","SDG 4","SDG 5", 
                          "SDG 6", "SDG 7", "SDG 8", "SDG 9", "SDG 10","SDG 11",
                          "SDG 12","SDG 13","SDG 14","SDG 15", "SDG 16", "SDG 17")
  for (j in (1:length(temp_df$Policy))){
    #loop over column names
    for(k in (3:19)){
      if(temp_df$Goal[j] == colnames(output_df)[[k]]){
        print(row_4_df[1,k])
        print(temp_df$Goal[j])
        row_4_df[1, k] <- temp_df$Goal[j]
        print(row_4_df[1,k])
      }
    }
  }
  output_df <- rbind(output_df, row_4_df)
}

output_df[output_df=="0"]<-""
output_df$'N. OF SDGs' = 17 - rowSums(is.na(output_df) | output_df == "" | output_df == " ")


##add categories to final df for new policies
categories <- read_excel("D:/Work_JRC/Mapping_2/Query/titles_codes_categories.xlsx", sheet = "folder_list")
colnames(categories) <- c('index','title','Policy','Hyperlink', 'Category')

output_df$Category <- categories$Category[match(output_df$POLICY, categories$Policy)]
output_df$Title <- categories$title[match(output_df$POLICY, categories$Policy)]
output_df$hyperlink <- categories$Hyperlink[match(output_df$POLICY, categories$Policy)]



#add categories for old policies
# categories <- read_excel("policies_categories_final.xlsx", sheet = "folder_list")
# output_df$Category <- categories$Category[match(output_df$POLICY, categories$Policy)]





# use write csv for using comma as separator
#write.csv(output_df,"table_pol_list.csv", row.names = FALSE)
# use write.csv2 for using semicolon as separator
write.csv2(output_df,"table-policies-sdgs_VdL_17122020.csv", row.names = FALSE)

