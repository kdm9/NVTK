library(tidyverse)
args = commandArgs(trailingOnly=TRUE)

read.delim(args[1]) %>%
    group_by(Scanner) %>%
    summarise(prop_success = mean(Result != "")) %>%
    ungroup() %>%
    arrange(-prop_success)
