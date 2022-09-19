library(shiny)
library(rhandsontable)
library(tidyverse)


ui <- fluidPage(

    titlePanel("PlateMate -- convert between plate layouts and 'long' tables"),

    fluidRow(wellPanel(
      radioButtons("format", "From/to:",
                   c("From 96 well to long format" = "from96",
                     "From long format to 96 wells" = "fromlong"))
    )),

    fluidRow(wellPanel(
      rHandsontableOutput("intbl"),
      actionButton(inputId="enter",label="Convert")
    )),

    fluidRow(wellPanel(
      rHandsontableOutput("outtbl"),
    ))
    
)

server <- function(input, output) {
    observeEvent(input$format, {
      if (input$format == "from96") {
        DF=as.data.frame(matrix("", nrow=8, ncol=12))
        rownames(DF) = LETTERS[1:8]
        colnames(DF) = as.character(1:12)
      } else {
        DF = expand.grid(row=LETTERS[1:8], col=1:12) %>%
          transmute(well=sprintf("%s%02d", row, col), value="")
      }
      output$intbl=renderRHandsontable(rhandsontable(DF,readOnly=F))
    })
    observeEvent(input$enter, {
      if (input$format == "from96") {
        DF = hot_to_r(input$intbl) %>%
          rownames_to_column()  %>%
          pivot_longer(-rowname) %>%
          transmute(well=sprintf("%s%02d", rowname, as.integer(name)), value)
      } else {
        DF = hot_to_r(input$intbl) %>%
          tidyr::extract(well, into=c("row", "col"), regex="([A-H])([0-9]+)")%>%
          pivot_wider(names_from=col, values_from=value) %>%
          column_to_rownames("row")
      }
      output$outtbl=renderRHandsontable(rhandsontable(DF,readOnly=F))
    })
}

shinyApp(ui = ui, server = server)