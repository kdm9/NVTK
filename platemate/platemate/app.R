library(shiny)
library(rhandsontable)
library(tidyverse)


ui <- fluidPage(

    titlePanel("PlateMate -- convert between plate layouts and 'long' tables"),

    fluidRow(wellPanel(
      numericInput("nplates", "How many plates:", 1),
      radioButtons("format", "From/to:",
                   c("From 96 well to long format" = "from96",
                     "From long format to 96 wells" = "fromlong"))
    )),

    fluidRow(wellPanel(
      uiOutput("plates"),
      actionButton(inputId="enter",label="Show Table")
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
      if (input$format == "from96") {
        output$plates = renderUI(lapply(seq_len(input$nplates), function(i) {
              ti = textInput(sprintf("plate%d_name", i), "Plate Name", "")
              ht = rHandsontableOutput(sprintf("plate%d_hot", i))
              fluidRow(wellPanel(ti, ht))
          }))
        for(i in seq_len(input$nplates)) { local({
          DF=as.data.frame(matrix("", nrow=8, ncol=12))
          colnames(DF) = as.character(1:12)
          rownames(DF) = LETTERS[1:8]
          intbl=renderRHandsontable(rhandsontable(DF, readOnly=F))
          output[[sprintf("plate%d_hot", i)]] <- intbl
        })}
      } else {
        DF = expand.grid(row=LETTERS[1:8], col=1:12,
                         plate_name=sprintf("p%i", seq_len(input$nplates))) %>%
          transmute(plate_name=as.character(plate_name), well=sprintf("%s%02d", row, col), value="")
        output$plates =renderUI(fluidRow(rHandsontableOutput("intbl")))
        output$intbl = renderRHandsontable(rhandsontable(DF,readOnly=F))
      }
    })
    observeEvent(input$enter, {
      if (input$format == "from96") {
        DF = do.call("bind_rows", lapply(seq_len(input$nplates), function(i){
          local({
            pl = hot_to_r(input[[sprintf("plate%d_hot", i)]]) %>%
              rownames_to_column()  %>%
              pivot_longer(-rowname) %>%
              transmute(
                        plate_name=input[[sprintf("plate%d_name", i)]],
                        well=sprintf("%s%02d", rowname, as.integer(name)),
                        value
                        ) %>%
              arrange(substr(well, 2, 4), well)
            return(pl)
          })
        }))
      } else {
        DF = hot_to_r(input$intbl) %>%
          dplyr::mutate(plate_name=as.character(plate_name)) %>%
          tidyr::extract(well, into=c("row", "col"), regex="([A-H])([0-9]+)")%>%
          pivot_wider(names_from=col, values_from=value)
      }
      str(DF)
      output$outtbl=renderRHandsontable(rhandsontable(DF,readOnly=T))
      
      output$dlBtn <- downloadHandler(
        filename = function(){"plates.csv"}, 
        content = function(fname){ write_csv(DF, fname, na="") }
      )
    })
}

shinyApp(ui = ui, server = server)
