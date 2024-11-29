library(shiny)
library(rhandsontable)
library(tidyverse)


ui <- fluidPage(
  
  titlePanel("TECANalyze -- quantifiy DNA with PicoGreen"),
  
  fluidRow(wellPanel(
    numericInput("nplates", "How many plates:", 1, min=1, max=12),
    checkboxInput("intercept", "Use an intercept in linear prediction model?", TRUE),
    checkboxInput("includestds", "Include standards in output table?", FALSE),
    checkboxInput("stdperplate", "Use standards only from each plate to quantify each plate", TRUE),
    splitLayout(
      numericInput("concA", "[Std A]:", 0,  width="100px"),
      numericInput("concB", "[Std B]:", 4,  width="100px"),
      numericInput("concC", "[Std C]:", 8,  width="100px"),
      numericInput("concD", "[Std D]:", 16, width="100px"),
      numericInput("concE", "[Std E]:", 20, width="100px"),
      numericInput("concF", "[Std F]:", 24, width="100px"),
      numericInput("concG", "[Std G]:", 32, width="100px"),
      numericInput("concH", "[Std H]:", 40, width="100px"),
      actionButton("reverse", "Reverse Standards"),
    )
  )),
  uiOutput("plates"),
  fluidRow(wellPanel(
    actionButton(inputId="enter",label="Convert"),
    downloadButton("dlBtn"),
    tableOutput("outtbl"),
    plotOutput("standardsPlot"),
    verbatimTextOutput("stdmdltxt")
  ))
)

server <- function(input, output, session) {
  observeEvent(input$reverse, {
    for (i in 1:4) {
      lhs = sprintf("conc%s", LETTERS[i])
      rhs = sprintf("conc%s", LETTERS[8-i+1])
      newR = input[[lhs]]
      newL = input[[rhs]]
      updateNumericInput(session, lhs, value=newL)
      updateNumericInput(session, rhs, value=newR)
    }
  })

  observeEvent(input$nplates, {
    output$plates = renderUI(lapply(seq_len(input$nplates), function(i) {
          ti = textInput(sprintf("plate%d_name", i), "Plate Name", "")
          ht = rHandsontableOutput(sprintf("plate%d_hot", i))
          msg=tags$p("In the bottom status row, write EXACTLY 'STD' to mark a column as the standard column, or the name of another plate to mark that this is the standard column from that plate")
          cb = checkboxGroupInput(sprintf("plate%d_stds", i), "Standard column(s)", choices=as.character(1:12), inline=T)
          col1s = fluidRow(wellPanel(
            tags$p("If this is a 'column 1s' plate, which plate name does each column belong to?"),
            splitLayout(
            textInput("col1of1", "1", ""), textInput("col1of2", "2", ""), textInput("col1of3", "3", ""), textInput("col1of4", "4", ""),
            textInput("col1of5", "5", ""), textInput("col1of6", "6", ""), textInput("col1of7", "7", ""), textInput("col1of8", "8", ""),
            textInput("col1of9", "9", ""), textInput("col1of10", "10", ""), textInput("col1of11", "11", ""), textInput("col1of12", "12", ""),
          ), width="800px"))
          fluidRow(wellPanel(ti, ht, msg))#,cb, col1s))
      }))
    for(i in seq_len(input$nplates)) { local({
      DF=as.data.frame(matrix("", nrow=9, ncol=12))
      colnames(DF) = as.character(1:12)
      rownames(DF) = c(LETTERS[1:8], "STATUS")
      intbl=renderRHandsontable(rhandsontable(DF, readOnly=F))
      output[[sprintf("plate%d_hot", i)]] <- intbl
    })}
    })
    
  observeEvent(input$enter, {
    data = do.call("bind_rows", lapply(seq_len(input$nplates), function(i){
      local({
        pname = input[[sprintf("plate%d_name", i)]]
        d = hot_to_r(input[[sprintf("plate%d_hot", i)]])
        rownames(d) = c(LETTERS[1:8], "status")
        pl = d %>%
            t() %>%
            as.data.frame() %>%
            rownames_to_column("col") %>%
            pivot_longer(LETTERS[1:8]) %>%
            transmute(plate_name=pname, col=as.integer(col), row=name, well=sprintf("%s%02d", name, col), value,
                      status=sub("^\\s+|\\s+$", "", status, perl=T))
        pl
      })
    }))

    if (input$stdperplate) {
        data$std_group=data$plate_name
    } else {
        data$std_group="everything"
    }

    stdconc = local({
        x = data.frame(row=LETTERS[1:8])
        x$conc = sapply(x$row, function(l) as.numeric(input[[sprintf("conc%s", l)]]))
        x
    })

    data2 = data %>%
        mutate(value=as.numeric(value)) %>%
        group_by(std_group) %>%
        group_modify(
            function(df, key) {
                stds = df %>%
                    filter(status=="STD") %>%
                    left_join(stdconc, by="row")
                if (input$intercept) {
                  m = lm(conc ~ value, data=stds)
                } else {
                  m = lm(conc ~ 0 + value, data=stds)
                }
                print(summary(m))
                res = df %>%
                    mutate(
                       conc=pmax(predict(m, df), 0),
                       r2=summary(m)$adj.r.squared,
                    )
                return(res)
            }) %>%
        ungroup()

    nonstd = data2 %>%
        filter(is.na(status) | status == "")
    stds = data2 %>%
        filter(status=="STD") %>%
        left_join(stdconc, by="row", suffix=c("", "_std")) %>%
        glimpse()
    colstds = data2 %>%
        filter(status %in% data2$plate_name)

    corrected_stdcols = colstds %>%
        group_by(plate_name, status) %>%
        summarise(src_col=unique(col)) %>%
        ungroup() %>%
        rename(src_plate=plate_name) %>%
        left_join(stds, ., by=c("plate_name"="status")) %>%
        filter(!is.na(src_plate)) %>%
        left_join(colstds, by=c("src_plate"="plate_name", "src_col"="col")) %>%
        mutate(well=sprintf("%s%02d", row, col))
    
    if (input$includestds) {
        stds_fortbl = data2 %>%
            filter(status=="STD") %>%
            group_by(plate_name) %>%
            mutate(col=NA, well=sprintf("std_%s_%i", row, stdconc[match(row, stdconc$row),"conc"]))
        data3 = bind_rows(nonstd, corrected_stdcols, stds_fortbl)
    } else {
        data3 = bind_rows(nonstd, corrected_stdcols)
    }
    data3 = data3 %>%
        select(plate_name, row, col, well, value, conc, r2)  %>%
        filter(!is.na(value)) %>%
        arrange(plate_name, col, row) %>%
        select(-row, -col) 

    output$dlBtn <- downloadHandler(
      filename = function(){"plates.csv"}, 
      content = function(fname){ write_csv(data3, fname, na="") }
    )
    output$outtbl=renderTable(data3)
    output$standardsPlot <- renderPlot({
        ggplot(stds, aes(conc_std, value)) + geom_point(aes(colour=plate_name)) + scale_colour_brewer() + theme_bw() +
            labs(colour="Plate", x="Std. Conc.", y="Fluroescence Value") +
            theme(
                  legend.position="bottom",
            )
    }, res = 200, width=1200, height=900)
  })
}

shinyApp(ui = ui, server = server)
