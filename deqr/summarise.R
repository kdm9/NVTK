library(tidyverse)
args = commandArgs(trailingOnly=TRUE)

read.delim(args[1]) %>%
    group_by(Scanner) %>%
    summarise(Success = mean(Result != ""), 
              Time = mean(Time),
              TimeSD = sd(Time)) %>%
    ungroup() %>%
    arrange(-Success) %>%
    knitr::kable()
