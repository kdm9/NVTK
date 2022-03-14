library(tidyverse)

read.delim("all.tsv") %>%
    group_by(Scanner) %>%
    summarise(prop_success = mean(Result != "None")) %>%
    ungroup() %>%
    arrange(-prop_success)
