library(shiny)
library(rhandsontable)
library(tidyverse)


ui <- fluidPage(
  
  titlePanel("TECANalyze -- quantifiy DNA with PicoGreen"),
  
  fluidRow(wellPanel(
    numericInput("nplates", "How many plates:", 2),
    checkboxInput("intercept", "Use an intercept in linear prediction model?", FALSE),
    splitLayout(
      numericInput("concA", "[Std A]:", 40, width="100px"),
      numericInput("concB", "[Std B]:", 32, width="100px"),
      numericInput("concC", "[Std C]:", 24, width="100px"),
      numericInput("concD", "[Std D]:", 20, width="100px"),
      numericInput("concE", "[Std E]:", 16, width="100px"),
      numericInput("concF", "[Std F]:",  8, width="100px"),
      numericInput("concG", "[Std G]:",  4, width="100px"),
      numericInput("concH", "[Std H]:",  0, width="100px"),
    )
  )),
  uiOutput("plates"),
  fluidRow(wellPanel(
    actionButton(inputId="enter",label="Convert"),
    tableOutput("outtbl"),
    plotOutput("standardsPlot"),
    verbatimTextOutput("stdmdltxt")
  ))
)

server <- function(input, output) {
  observeEvent(input$nplates, {
    output$plates = renderUI(lapply(seq_len(input$nplates), function(i) {
          ti = textInput(sprintf("plate%d_name", i), "Plate Name", "")
          ht = rHandsontableOutput(sprintf("plate%d_hot", i))
          cb = checkboxGroupInput(sprintf("plate%d_stds", i), "Standard column(s)", choices=as.character(1:12), inline=T)
          fluidRow(wellPanel(ti, ht,cb))
      }))
    for(i in seq_len(input$nplates)) { local({
      DF=as.data.frame(matrix("", nrow=8, ncol=12))
      colnames(DF) = as.character(1:12)
      rownames(DF) = LETTERS[1:8]
      intbl=renderRHandsontable(rhandsontable(DF, readOnly=F))
      output[[sprintf("plate%d_hot", i)]] <- intbl
    })}
    })
    
  observeEvent(input$enter, {
    data = do.call("bind_rows", lapply(seq_len(input$nplates), function(i){
      local({
        pname = input[[sprintf("plate%d_name", i)]]
        d = hot_to_r(input[[sprintf("plate%d_hot", i)]]) %>%
          mutate(row=LETTERS[1:8]) %>%
          pivot_longer(!c("row")) %>%
          transmute(plate_name=pname, well=sprintf("%s%02d", row, as.integer(name)), value, col=name, row)
        d
      })
    }))
    stds = do.call("bind_rows", lapply(seq_len(input$nplates), function(i){
      local({
        if (length(input[[sprintf("plate%d_stds", i)]]) > 0) {
        return(data.frame(plate_name=input[[sprintf("plate%d_name", i)]],
                          std_cols=input[[sprintf("plate%d_stds", i)]]))
        }
      })}))
    
    std_concs = do.call("bind_rows", lapply(LETTERS[1:8], function(w) {
      local({
        data.frame(well=w, conc=input[[sprintf("conc%s", w)]])
      })
    }))
    data = mutate(data, value=as.numeric(value))
   
    std = left_join(stds, data, by=c("plate_name", "std_cols"="col")) %>%
      left_join(std_concs, by=c("row"="well")) %>%
      mutate(conc=as.numeric(conc), value=as.numeric(value))
    
    
    if (input$intercept) {
      m = lm(conc ~ value, data=std)
    } else {
      m = lm(conc ~ 0 + value, data=std)
    }

    
    data2 = data %>%
      transmute(plate_name, well, rfu=value, conc=predict(m, data)) %>%
      filter(!is.na(rfu)) %>%
      mutate(conc = ifelse(conc < 0, 0, conc))
    
    output$standardsPlot = renderPlot(
      ggplot(std, aes(conc, value)) +
        geom_point(data=std) +
        geom_point(aes(conc, rfu), colour="red", data=data2) +
        labs(x="Conc (ng/uL)", y="RFU", title="Standard Curve") +
        theme_classic()
    )
    output$stdmdltxt = renderPrint(summary(m))
    output$outtbl=renderTable(data2)
  })
}

shinyApp(ui = ui, server = server)
