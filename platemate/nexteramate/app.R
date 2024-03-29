library(shiny)
library(rhandsontable)
library(tidyverse)
library(Biostrings)
i7s = read_csv("i7s.csv")
i5s = read_csv("i5s.csv")

ui <- fluidPage(

    titlePanel("Nexteramate -- Combine sample plate layouts into a sample sheet"),

    fluidRow(wellPanel(
      numericInput("nplates", "How many plates:", 1),
      radioButtons("format", "From/to:",
                   c("From 96 well grid format" = "from96",
                     "From \"tidy\"/long format" = "fromlong")),
      checkboxInput("revcom_i5", "Reverse-complement i5 sequence (YES: NextSeq pre 2020-ish, HiSeq X, HiSeq 3000/4000 and NovaSeq 6000 v1.5+; NO: NextSeq after 2020-ish, Miseq, Hiseq2000/2500):", T),
      checkboxInput("revcom_i7", "Reverse-complement i7 sequence (YES for all common applications):", T),
      p("TLDR: modern machines: RC both, older kits: i7 RC, i5 FWD. To explain the revcomp options: the indices included in this tool match exactly the oligos we ordered. Because of how the sequencing happens, Illumina acutally sequences at least the i7 index reverse-complemented with respect to the oligos. In modern sequencing kits, both i5 and i7 will be RC, but with older kits, i5 is 'normal' but i7 is RC. Confusingly, the illumina documentation refers i5F/i7R as 'forward strand', but says you need to revcomp it compared to the typical usage (which is true, sorta). See", a("this", href='https://teichlab.github.io/scg_lib_structs/methods_html/Illumina.html')),
      p("For MPI Tü folks: The NextSeq at the Genome Centre is new enough to want the only the i7 reverse complimented. Therefore: i5 = NO, i7 = YES."),
      checkboxInput("blank2well", "Replace empty wells with plate name & well", T),
    )),

    fluidRow(wellPanel(
      uiOutput("plates"),
      actionButton(inputId="enter",label="Compute Sample Sheet")
    )),

    fluidRow(wellPanel(
      downloadButton("dlBtn"),
      rHandsontableOutput("outtbl"),
    ))
) 
server <- function(input, output) {
    paramsChanged <- reactive({
        list(input$format, input$nplates)
    })
    observeEvent(paramsChanged(), {
        if (!is.na(input$nplates) & is.numeric(input$nplates)) {
            output$plates = renderUI(lapply(seq_len(input$nplates), function(i) {
                    ti = textInput(sprintf("plate%d_name", i), "Plate Name", "")
                    sf = textInput(sprintf("plate%d_suffix", i), "Sample Name Suffix", "")
                    i7 = selectInput(sprintf("plate%d_i7", i), "i7", unique(i7s$i7))
                    i5 = selectInput(sprintf("plate%d_i5", i), "i5", unique(i5s$i5))
                    ht = rHandsontableOutput(sprintf("plate%d_hot", i))
                    fluidRow(wellPanel(ti, sf, i7, i5, ht))
            }))
        if (input$format == "from96") {        
            for(i in seq_len(input$nplates)) { local({
                DF=as.data.frame(matrix("", nrow=8, ncol=12))
                colnames(DF) = as.character(1:12)
                rownames(DF) = LETTERS[1:8]
                intbl=renderRHandsontable(rhandsontable(DF, readOnly=F))
                output[[sprintf("plate%d_hot", i)]] <- intbl
                })}
        } else {
            for(i in seq_len(input$nplates)) { local({
                DF = expand.grid(row=LETTERS[1:8], col=1:12) %>%
                      transmute(well=sprintf("%s%02d", row, col), sample_id="")
                intbl=renderRHandsontable(rhandsontable(DF, readOnly=F))
                output[[sprintf("plate%d_hot", i)]] <- intbl
            })}
        }
    }})
    observeEvent(input$enter, {
        if (input$format == "from96") {
            DF = do.call("bind_rows", lapply(seq_len(input$nplates), function(i){ local({
                pl = hot_to_r(input[[sprintf("plate%d_hot", i)]]) %>%
                    rownames_to_column()  %>%
                    pivot_longer(-rowname) %>%
                    transmute(
                              plate_name=input[[sprintf("plate%d_name", i)]],
                              i7=input[[sprintf("plate%d_i7", i)]],
                              i5=input[[sprintf("plate%d_i5", i)]],
                              well=sprintf("%s%02d", rowname, as.integer(name)),
                              sample_id=ifelse(input$blank2well & (is.na(value) | value == "" | value == "blank"),
                                               sprintf("blank_%s_%s", plate_name, well),
                                               paste0(value, input[[sprintf("plate%d_suffix", i)]])),
                              ) %>%
                    arrange(substr(well, 2, 4), well) %>%
                    left_join(i7s) %>%
                    left_join(i5s)
               return(pl)
            })}))
        } else {
            DF = do.call("bind_rows", lapply(seq_len(input$nplates), function(i){ local({
                pl = hot_to_r(input[[sprintf("plate%d_hot", i)]]) %>%
                    transmute(
                              plate_name=input[[sprintf("plate%d_name", i)]],
                              i7=input[[sprintf("plate%d_i7", i)]],
                              i5=input[[sprintf("plate%d_i5", i)]],
                              well = sub("^([A-H])([0-9])$", "\\10\\2", well),
                              sample_id
                              ) %>%
                    arrange(substr(well, 2, 4), well) %>%
                    left_join(i7s) %>%
                    left_join(i5s)
               return(pl)
            })}))
        }
	print(DF)
        if (input$revcom_i5) {
            DF$index.i5 = sapply(DF$index.i5, function(s) {as.character(Biostrings::reverseComplement(Biostrings::DNAString(s)))})
        }
        if (input$revcom_i7) {
            DF$index.i7 = sapply(DF$index.i7, function(s) {as.character(Biostrings::reverseComplement(Biostrings::DNAString(s)))})
        }
        output$outtbl=renderRHandsontable(rhandsontable(DF,readOnly=T))
        
        output$dlBtn <- downloadHandler(
          filename = function(){"samplesheet.csv"}, 
          content = function(fname){ write_csv(DF, fname, na="") }
        )
    })
}

shinyApp(ui = ui, server = server)
