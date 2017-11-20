from os.path import dirname, join
from datetime import datetime, date, timedelta
import pandas as pd
from bokeh.layouts import row, widgetbox, layout
from bokeh.models import ColumnDataSource,CheckboxButtonGroup, CustomJS, DatetimeTickFormatter, FuncTickFormatter
from bokeh.models.widgets import DatePicker, Select, DateRangeSlider, RadioGroup, RangeSlider, Button, DataTable, TableColumn, DateFormatter
from bokeh.io import curdoc
from urllib.request import urlopen
from bokeh.plotting import figure
from bokeh.io import output_file, show
import numpy as np
import emoji

#cd C:\Users\asher\Documents\GitHub\data602-finalproject 
#bokeh serve HistoricalDashboard.py --show


# Colors for plotting Counters
colors = ['red', 'green', 'blue', 'orange', 'black', 'grey', 'brown',
                   'cyan', 'yellow', 'purple']

# Counter locations for displaying to user
counterNames = ["2nd Ave", "26th Ave", "39th Ave", "Burke Gilman Trail", "Broad", 
                "Elliot", "Fremont Bridge",
                "MTS Trail", "NW 58th St",  "Spokane St"]

# Dictionary for converting full trail names to column numbers
counterDict = {"Burke Gilman Trail":0,
               "Broad": 1,
               "Elliot": 2,
               "Fremont Bridge": 3,
               "MTS Trail": 4,
               "NW 58th St": 5,
               "2nd Ave": 6,
               "Spokane St": 7,
               "39th Ave": 8,
               "26th Ave": 9}

# Weather Coding Dictionary
weatherDict = {0:"None", 
               1: "Fog", 
               2: "Rain", 
               3: "Snow",
               4:"Thunderstorm"}

# Get dataframe of historical observations, weather, and daylight hours
histPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/histDF.csv"
weatherPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/weatherDF.csv"
daylightPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/daylightDF.csv"

# Local path for testing
#histPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/histDF.csv"
#weatherPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/weatherDF.csv"
#daylightPath = r"C:\Users\asher\Documents\GitHub\data602-finalproject/daylightDF.csv"

#jsPath = "https://raw.githubusercontent.com/cspitmit03/data602-finalproject/master/download.js"

histDF = pd.read_csv(histPath, index_col = 0) # From Seattle Data Portal
weatherDF = pd.read_csv(weatherPath, index_col = 0) # From WeatherUnderground
daylightDF = pd.read_csv(daylightPath, index_col = 0) # From jakevdp formula

# Set indices of hist and weather as datetime & date objects, respectively
Indx = [] # Index to house dates
for i in range(len(histDF)): 
    Indx.append(datetime.strptime(histDF.index[i], '%m/%d/%Y %H:%M'))
histDF.index = Indx
#histDF.index = histDF.index.to_pydatetime()

Indx = [] # Index to house dates
for i in range(len(weatherDF)): 
    Indx.append(datetime.strptime(weatherDF.index[i], '%Y-%m-%d').date())
weatherDF.index = Indx

Indx = [] # Index to house hours of daylight per day
for i in range(len(daylightDF)): 
    Indx.append(datetime.strptime(daylightDF.index[i], '%Y-%m-%d').date())
daylightDF.index = Indx

MyTools = "pan,hover,wheel_zoom,box_zoom,reset,undo,save"

def subsetMonth(monthList, df=histDF):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.month.isin(monthList)]

def subsetWeekday(daylist, df=histDF):
    # Return dataframe containing only the days of the week specified,
    # where 0 = Monday, 1 = Tuesday, etc.
    return df[df.index.weekday.isin(daylist)]

def subsetHours(start, end, df=histDF):
    # Return dataframe within the times specified, in 24 hour format
    # e.g. start = '12:00', end = '13:00'
    start = str(int(start)) + ":00"
    end = str(int(end)) + ":00"
    df = df.between_time(start, end)
    return df

def subsetRain(low = 0, high = 2.5, wdf = weatherDF, df = histDF):
    # Subset histDF by specified rain volume, inches per day
    
    dfDates = pd.Series(df.index.date) # All dates in dataset
    
    filterDates = [] # List to store dates meeting filters
    
    # Create list of lists of dates satisfying filters
    filterDates = wdf[(wdf.Precip >= low) & 
                      (wdf.Precip <= high)].index 
        
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))
    
    # Return dataframe containing only the dates that meet the filter criteria    
    return df[filterBools]

def subsetWeather(weatherList, wdf = weatherDF, df = histDF):
    # Return dataframe containing only dates where the specified weather events
    # occurred. Eg, subsetWeather(["Rain", "Snow"]) returns all counts from days
    # on which it rained or snowed. If no events, string should be "None"
    # 
    # Note, if there were also fog on a given day, 
    # that date would show up in the returned dataframe.
    
    # Set weather Events field null values to empty strings
    wdf.Events = wdf.Events.replace(np.nan, 'None', regex=True)
    
    # Dates with the specified weather conditions
    dfDates = pd.Series(df.index.date) # All dates in dataset
    
    filterDates = [] # List to store dates meeting filters
    
    # Create list of lists of dates satisfying filters
    for event in weatherList:
        filterDates.append(wdf.index[wdf['Events'].str.contains(event)])
    
    # Convert list of lists into flat list
    filterDates = [item for sublist in filterDates for item in sublist]
    
    # Sort dates list
    filterDates.sort()    
        
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))
    
    # Create new dataframe containing only the dates that meet the filter criteria
    filterDF = df[filterBools]
    
    return filterDF

def subsetDaylight(df = histDF, ddf = daylightDF, low=8, high=16):
    # Function for filtering dataset by hours of sunlight for each date
    
    # Create list of dates that meet filter criteria
    filterDates = ddf[(ddf.daylightHours >= low) & 
                      (ddf.daylightHours <= high)].index
    
    dfDates = pd.Series(df.index.date) # All dates in dataset
     
    # Obtain list of booleans indicating whether a date meets the filter criteria
    filterBools = list(dfDates.isin(filterDates))

    # Return dataframe containing only the dates that meet the filter criteria    
    return df[filterBools] 

def plotTypicalDay(df = histDF): 
    
    # Aggregate data by hour of the day
    df = df.groupby([df.index.hour])[df.columns].mean()
    
    # Create x-axis values from index which contains hours
    xs = df.index*1000*60*60 # Convert milliseconds to hours
        
    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Count By Hour for One Day")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%a %-I %p')
    
    # show(p)
    return p

def plotTypicalWeek(df = histDF): 
    # Plots average count by hour and day of week
    
    # Aggregate data by day of the week and hour
    df = df.groupby([df.index.weekday, df.index.hour])[df.columns].mean()

    # Create x-axis values from index which contains hours
    #xs = pd.Series(range(len(df)))*1000*60*60 # Convert milliseconds to hours
    xs = (np.array(range(len(df))) + 4*24)*1000*60*60
    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Count By Hour, for One Week")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(hours = '%a %-I %p',
                                                     days = '%a')
    
    show(p)
    return

def plotTypicalYear(df = histDF):
    # Plots average count of one full typical year

    # Aggregate data by day of the week and hour
    df = df.groupby([df.index.week])[df.columns].mean()

    # Create x-axis values from index which contains hours
    xs = (df.index - 1) * 1000*60*60*24*7

    p = figure(plot_width = 800, tools = MyTools, 
               title = "Average Bicycle Counts By Week, for One Year")
    for i in range(len(df.columns)):
        p.line(xs, df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(months = '%B')
    show(p)
    return

def plotHistory(df = histDF):
    # Plots entire history
    
    # Downsample into one week segments
    df = df.resample('7d').sum()

    p = figure(plot_width = 800, tools = MyTools, 
               title = "Historical Bicycle Counts By Week")
    for i in range(len(df.columns)):
        p.line(x = df.index,y = df.iloc[:,i], color= colors[i], legend= df.columns[i])
        p.xaxis[0].formatter = DatetimeTickFormatter(months = '%B',
                                                     years = '%Y')
    show(p)
    return 

def TypicalDay(df = histDF):
    df = df.groupby([df.index.hour])[df.columns].mean()
    return df

def TypicalWeek(df = histDF):
    df = df.groupby([df.index.weekday, df.index.hour])[df.columns].mean()
    
    indx = np.array([])
    for i in range(len(df.index)):
        indx = np.append(indx, df.index[i][0]*24 + df.index[i][1] + 4*24)
    
    df.index = indx
    return df

def TypicalYear(df = histDF):
    # Calculate the historical weekly sum
    df = df.resample('7D').sum()
    
    # Convert each date to a week number
    df.index = df.index.week

    # Average counts by week number
    df = df.groupby(df.index).mean()
    
    # Last week is only one day, so exclude it
    df = df.iloc[0:52, :]
    
    # Convert indices to start at 0 instead of 1
    df.index = list(range(52))
    
    return df

# Set up data
mydf = TypicalDay()  
x =  np.array(mydf.index)*1000*60*60
#x = list(np.array(range(24))*1000*60*60)
y = mydf.Fremont
source = ColumnDataSource(data=dict(x=x, y=y))

# Set up plot
plot = figure(plot_height=600, plot_width=750, title="Bicycle Counts",
              tools=MyTools, y_range=[0,800])
              #x_range=[0, 23]
plot.xaxis.axis_label = "Date/Time" # x axis label
#plot.xaxis.ticker = list(np.array([0, 6, 8, 10, 12, 14, 16, 18, 20, 
#                              22]*1000*60*60)) # x axis tick marks
plot.xaxis.formatter = DatetimeTickFormatter(hours = ['%I %p'], days = ['%a'])
plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


# Widgets section

# Drop down for selecting viewing a typical week or typical day
ViewDropdown = Select(title = "View by Average...", value = "Day",
              options = ["Day", "Week", "Year", "Historical"])

CounterDropdown = Select(title = "Select Counter", value = "Fremont Bridge", 
                             options = counterNames)

YearBoxes = CheckboxButtonGroup(labels = ["2012","'13", "'14", "'15", "'16", 
                                          "2017"], 
                         active=list(range(6)))

MonthBoxes = CheckboxButtonGroup(labels = ["Jan", "Feb", "March", "April", 
                                           "May", "June", "July", "Aug", "Sep",
                                           "Oct", "Nov", "Dec"], 
                                 active = list(range(12)))
WeekdayBoxes = CheckboxButtonGroup(labels = ["Mo", "Tu", "We",
                                              "Th", "Fr", "Sa",
                                              "Su"], 
                                   active=list(range(7)))
HourSlider = RangeSlider(title="Hour Range", start=0, end=23, value=(0, 23), 
                         step=1, format='0')

DaylightSlider = RangeSlider(title = "Hours of Daylight", start = 8, end = 16, 
                             value = (8,16), step = 1, format = "0")

WeatherBoxes = CheckboxButtonGroup(labels = [emoji.emojize(':sunny: :cloud:', use_aliases=True), 
                                             emoji.emojize('fog :foggy:', use_aliases=True), 
                                             emoji.emojize(':umbrella:', use_aliases=True), 
                                             emoji.emojize(':snowflake:', use_aliases=True), 
                                             emoji.emojize(':zap:', use_aliases=True), 
                                             ], 
                                   active = [0,1,2,3,4])

RainSlider = RangeSlider(title="Inches of Rain per Day", start = 0, end = 2.5, 
                         value = (0,2.5), step = 0.05, format = "0.00")

# Set up callbacks
def update_data(attrname, old, new):

    # Get the current slider values
    view = ViewDropdown.value
    counter = counterDict[CounterDropdown.value]
    start = YearBoxes.active[0] + 2012
    end = YearBoxes.active[-1] + 2012
    months = MonthBoxes.active
    weekdays = WeekdayBoxes.active
    hours = np.round(HourSlider.value)
    weather = WeatherBoxes.active
    light = DaylightSlider.value
    rain = RainSlider.value

    # Translate weather list of ints to list of strings, eg ["Fog", "Rain"]
    weatherList = []
    for i in weather: weatherList.append(weatherDict[i])

    # Convert start and end from ints to datetime 
    # due to Bokeh bug: https://github.com/bokeh/bokeh/issues/6895#event-1242295796
    yearRange = list(range(start, end + 1))

    # Generate the new dataframe
    mydf = histDF.copy(deep = True)
    mydf = mydf.loc[mydf.index.year.isin(yearRange)] # Subset dates 
    mydf = mydf[mydf.index.month.isin(months)] # Subset months
    mydf = mydf[mydf.index.weekday.isin(weekdays)] # Subset weekdays 
    mydf = subsetHours(start = hours[0], end = hours[1], df = mydf) # Subset hours
    mydf = subsetDaylight(df = mydf, low = light[0], high = light[1])
    mydf = subsetWeather(weatherList, df = mydf)
    mydf = subsetRain(df = mydf, low = rain[0], high = rain[1])
    

    if view == "Year": # Year view has counts by week
        mydf = TypicalYear(df = mydf)
        x = np.array(mydf.index)*1000*60*60*24*7 # Convert ms to weeks
    else: # For weekly and daily views, which have counts by hour
        if view == "Week":
            mydf = TypicalWeek(df = mydf)
        else:
            mydf = TypicalDay(df = mydf)
        x =  np.array(mydf.index)*1000*60*60 # Convert ms to hours
        
    
    y = mydf.iloc[:, counter].astype(float)
    
    #if counter == 3:
    #    plot.plot_height = 800
    #else:
    #    plot.plot_height = 400
    
    #x =  np.array(mydf.index)*1000*60*60 # Convert ms to hours
    
    #x = range(int(hours[0]),int(hours[1] + 1)) 
    #y = TypicalDay(mydf).iloc[:, counter].astype(float)
    #x = np.array(range(int(hours[0]),int(hours[1] + 1)))*7
        
    source.data = dict(x=x, y=y)
    
for w in [ViewDropdown, HourSlider, DaylightSlider, RainSlider, CounterDropdown]:
    w.on_change('value', update_data)
    
for z in [YearBoxes, MonthBoxes, WeekdayBoxes, WeatherBoxes]:
    z.on_change('active', update_data)

# Set up layouts and add to document
inputs = widgetbox(ViewDropdown, CounterDropdown, YearBoxes, MonthBoxes, WeekdayBoxes, 
                   HourSlider, DaylightSlider, WeatherBoxes, RainSlider)


lay = layout([
        [inputs, plot]
        ], sizing_mode = 'fixed')
#curdoc().add_root(row(inputs, plot, width=800))
curdoc().add_root(lay)    
curdoc().title = "Bicycle Counts"

