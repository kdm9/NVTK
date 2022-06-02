# ---
# jupyter:
#   jupytext:
#     formats: ipynb,R:light
#     text_representation:
#       extension: .R
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.13.8
#   kernelspec:
#     display_name: R
#     language: R
#     name: ir
# ---

library(tidyverse)

meta = read_tsv("updated_paco_mapping.tsv")

spec(meta)

meta %>%
    select(individual=paco_id, locality_name=locality, lat=site_lat, lon=site_lon, datetime) %>%
    filter(!is.na(lat), !is.na(locality_name)) %>%
    write_tsv("meta_for_web.tsv", na = "")
