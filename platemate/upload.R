rsconnect::setAccountInfo(name='kdm9', token=Sys.getenv("RS_TOKEN"), secret=Sys.getenv("RS_SECRET"))
rsconnect::deployApp(appDir="platemate", appName="platemate")
rsconnect::deployApp(appDir="tecanalyze", appName="tecanalyze")
