# Run this app with `python3 met_visualization_project.py` and
# visit http://127.0.0.1:8050/ in your web browser.
#
# Note: MetObjects.csv is a CSV file containing data about the collection of
# the Metropolitan Museum of Art.  It can be accessed at
# https://github.com/metmuseum/openaccess

from dash import Dash, dcc, html, get_asset_url
import plotly.express as px
import pandas as pd
import numpy as np
import re

pd.options.mode.chained_assignment = None
background_color = "#f2f3e4"
app = Dash(__name__)

# let's just use the parts of this we actually need

df = pd.read_csv("MetObjects.csv", 
    usecols=[
        "Object Number", 
        "AccessionYear",
        "Department",
        "Culture",
        "Country",
        "Is Highlight",
        ],
    dtype=str,
    )

# Drop the Libraries because it is not clear what is included
# in that category - it does not clearly correspond to any
#  department

df["Department"] = df['Department'].astype(str)
df = df.drop(df[(df['Department'] == "The Libraries")].index)

# This adds a cleaned Accession Year column of years (and NaNs) to the dataframe, since
# the data was mixed
cleaned_year_list = []

for entry in df["AccessionYear"]:
    entry = str(entry)
    pattern = re.compile(r'[0-9]{4}')
    result = pattern.search(entry)
    try: 
      cleaned_year_list.append(result[0])   
    except:
        result = None
        cleaned_year_list.append("")

df["Cleaned Accession Year"] = cleaned_year_list   

# To be able to do comparison operations, we need this to be a numeric column
df['Cleaned Accession Year'] = pd.to_numeric(df['Cleaned Accession Year'], errors='coerce')

# We need to clean up the location data since there are multiple places that 
# data could be entered (and it might not exist at all.)

def clean_country_info_column(row):
    row['Country'] = str(row['Country'])
    row['Culture'] = str(row['Culture'])
    if not row['Country'] and not row['Culture']:
        return np.nan
    elif not row['Country']:
        return row['Culture']
    else:
        return row['Country']

df["Location"] = df.apply(clean_country_info_column, axis=1)

# We need a dataframe with the total number of objects by department
dept_info = df['Department'].value_counts().rename_axis('Department Name').reset_index(name='Total Objects')
dept_info.sort_values(by=["Department Name"])

# Bar chart for total number of objects by department
fig1 = px.bar(dept_info.sort_values(by=["Department Name"], ascending=False), 
             x="Total Objects", y="Department Name",
#             labels={"Total Objects": "Total number of objects in 2023"}
             )

# Make nicer axes

fig1.update_layout(
    xaxis_tickformat = ',', 
    paper_bgcolor=background_color,)

# Let's get the total number of objects owned in 1923 by department. 
filtered_values = df.loc[df['Cleaned Accession Year'] <= 1923]
filtered_values_dept = filtered_values['Department'].value_counts().rename_axis('Department Name').reset_index(name='Total Objects in 1923')
filtered_values_dept.sort_values(by=["Department Name"])

# graph it and make nicer axes
fig2 = px.bar(filtered_values_dept.sort_values(by=["Department Name"], ascending=False), 
             x="Total Objects in 1923", y="Department Name",
             labels={"Total Objects in 1923": "Total Objects"}
             )

fig2.update_layout(
    xaxis_tickformat = ',',
    paper_bgcolor=background_color,)

# Let's find out how many objects were acquired each year by a given department
# Start by making a data frame that only has the relevant info we care about
acquisition_df = df[['Department', 'Cleaned Accession Year']]

# count how many objects per year per department 
acquisition_numbers = acquisition_df.groupby('Department')[["Cleaned Accession Year"]].value_counts()

# turn it into a dataframe
numbers_df = acquisition_numbers.reset_index()

# Drop the Robert Lehman Collection because all of it was obtained in one year, so not interesting
numbers_df["Department"] = numbers_df['Department'].astype(str)
numbers_df = numbers_df.drop(numbers_df[(numbers_df['Department'] == "Robert Lehman Collection")].index)

# give the count column a name (and the other one a better name)
numbers_df.rename(columns={"Cleaned Accession Year": "Year Acquired",
                           0 : "Number of Objects"}, inplace=True)

# sort by year  
numbers_sorted = numbers_df.sort_values(by=["Year Acquired"])
 
# We are going to want some custom colors to represent all of these departments
# since the default dictionary is too short and the colors start repeating
my_colors=['#f06292','#64ffda','#ef9a9a','#ff5722','#004d40','#ba68c8',
           '#536dfe','#eeff41','#558b2f','#00acc1', '#66bb6a','#b388ff',
           '#80d8ff','#9fa8da','#0d47a1','#6a1b9a','#b71c1c','#f9a825','#795548','#616161']

# graph it and make nicer axes
fig3 = px.line(numbers_sorted, x="Year Acquired", y="Number of Objects", color="Department", 
               color_discrete_sequence= my_colors, labels = {"Year Acquired": "Acquisition Year",})
fig3.update_layout(xaxis_tick0 = 1870, xaxis_dtick=5)
fig3.update_layout(yaxis_tickformat = ',',  paper_bgcolor=background_color,)


# Let's find out how many objects were acquired each decade by a given department
# Start by making a data frame that only has the relevant info we care about

acquisition_df = df[['Department', 'Cleaned Accession Year']]
acquisition_df = acquisition_df.dropna(subset="Cleaned Accession Year")

# We need to turn years into decades
acquisition_df['Decade'] = (acquisition_df['Cleaned Accession Year']//10) * 10

# count how many objects per decade per department 
acquisition_numbers = acquisition_df.groupby('Department')[["Decade"]].value_counts()

# turn it into a dataframe
numbers_df = acquisition_numbers.reset_index()

# Drop the Robert Lehman Collection because all of it was obtained in one year, so not interesting
numbers_df["Department"] = numbers_df['Department'].astype(str)
numbers_df = numbers_df.drop(numbers_df[(numbers_df['Department'] == "Robert Lehman Collection")].index)

# give the count column a name (and the other one a better name)
numbers_df.rename(columns={"Decade": "Decade Acquired",
                           0 : "Number of Objects"}, inplace=True)

# sort by year  
numbers_sorted = numbers_df.sort_values(by=["Decade Acquired"])
numbers_sorted["Decade Acquired"] = numbers_sorted["Decade Acquired"].astype('category')

pretty_decade_labels = []
for entry in numbers_sorted["Decade Acquired"]:
    new_entry = str(entry).replace(".0", "s")
    pretty_decade_labels.append(new_entry)

numbers_sorted["Pretty Decade"] = pretty_decade_labels

# Since there is no way to control the legend order in Dash, we need to 
# re-order our color list if we want to ensure the colors of the departments
# are consistent between these two graphs. 
my_colors_sorted = ['#f06292','#00acc1','#004d40','#64ffda','#ef9a9a',
                    '#b388ff','#66bb6a','#ba68c8','#ff5722','#536dfe', 
                    '#eeff41','#558b2f','#6a1b9a','#0d47a1','#80d8ff',
                    '#9fa8da','#b71c1c','#f9a825','#795548','#616161']

# graph it and make nicer axes

fig4 = px.bar(numbers_sorted, x="Pretty Decade", y="Number of Objects", color="Department",
              labels = {"Pretty Decade": "Acquisition by Decade",},
               color_discrete_sequence= my_colors_sorted)
fig4.update_layout(yaxis_tickformat = ',',  paper_bgcolor=background_color,)

# Let's make a geographic map of the museum's highlights

df["Is Highlight"] = df["Is Highlight"].astype(str)
highlight_values = df.loc[df['Is Highlight'] == "True"]

# Now we need to clean the data up so that we can use the ISO standard to map it
# The badly formatted data comes in a number of variations so we 
# have clauses written to handle them

def check_against_iso(country):
    try:
       country = pycountry.countries.search_fuzzy(country)
       return True
    except:
       return False


def clean_up_location_problems(entry):
    entry = str(entry)
    discards = set(["or", "and", "(?)", "probably"])
    directions = set(["Northern", "Western", "Sothern", "Southern", "South", "Central", "Lower"])
    islands = ['Tahiti', 'Mangareva']
    outliers = {
        'Democratic Republic of the Congo': 'Congo (the Democratic Republic of the)',  
        'Tibet': 'China', 
        'Iran (Persia)': 'Iran', 
        'New Spain (Mexico)': 'Mexico'}
    if '|' in entry:
        parts = entry.split('|')
        if len(list(set(parts))) == 1:
            entry = parts[0]
            cleaned_location = entry
        else:
            cleaned_location = np.nan
    elif set(entry.split()).intersection(discards):
        cleaned_location = np.nan
    elif set(entry.split()).intersection(directions):
        cleaned_location = entry.split()[1]
    elif entry == "England":
        cleaned_location = "United Kingdom"
    elif "present-day" in entry.split():
        cleaned_location = entry.split()[1]
    elif "formerly" in entry:
        cleaned_location = entry.split()[0]
    elif entry in islands:
        cleaned_location = "French Polynesia"
    elif entry in outliers.keys():
        cleaned_location = outliers[entry]
    else:
        cleaned_location = np.nan
    
    return(cleaned_location)

unique_locations = highlight_values['Location'].unique()
problem_locations = []

for entry in unique_locations:
    entry = str(entry)
    if check_against_iso(entry) == False:
        problem_locations.append(entry)

improved_locations = []

for entry in highlight_values['Location']:
    entry = str(entry)
    if entry in problem_locations:
        cleaned_location = clean_up_location_problems(entry)
        improved_locations.append(cleaned_location)
    else:
        improved_locations.append(entry)


highlight_values["Improved Location"] = improved_locations

# Get rid of the rows where we could not successfully clean the country data
highlight_values= highlight_values.dropna(subset="Improved Location")

# Now we can get the number of objects per country
highlight_numbers = highlight_values["Improved Location"].value_counts().rename_axis("Country of Origin").reset_index(name="Highlights")

# Graph it and make it pretty
fig5 = px.scatter_geo(highlight_numbers, locations="Country of Origin", 
                      hover_data={"Highlights": True, "Country of Origin": False}, hover_name="Country of Origin",
                      locationmode = "country names", 
                      )

fig5.update_layout(
    paper_bgcolor=background_color,
    plot_bgcolor=background_color,
    geo = dict(
        projection_type="orthographic",
        showcoastlines=True,
        landcolor="#f3ee97",
        showland=True,
        showocean = True,
        showlakes = False,
        oceancolor = "#97cff3",
        showcountries = True,
        fitbounds="locations",
        bgcolor=background_color,
    ),
    height=426, 
    width=426,
    title=dict(
        text="Map of Global Highlights",
        y = 0.05,
        x = 0.5,
        font=dict(
            family="Serif",
            size=16,
            color="black"
        ), 
    )

)

fig5.update_traces(marker=dict(color="Red", size=5))

# Turn all of this work into something displayed


opening_text = """

[The Metropolitan Museum of Art](https://www.metmuseum.org/) was founded 
in 1870 and is the largest art museum in the United States.  Its collection
has nearly half a million objects that span 5000 years of 
history.  This page presents some interesting data visualizations of
the museum's collection.  All of this data has been taken from the 
collection data the museum provides to the public on its 
[GitHub Open Access](https://github.com/metmuseum/openaccess) page.
"""
collections_text = """
These two bar charts show how many objects each department of the museum
contained in 1923 and in 2023.  While it is no surprise that the collection
has grown significantly in the last hundred years, it is interesting to 
see the change in how its collection is distributed.  "Drawings and
Prints" has not only retained its top position in overall collection size,
it clearly dwarfs all other contenders! 
"""
acquisitions_over_time_text = """
This messy-looking chart represents the number of acquisitions each department
has made over the entirety of the museum's history.  Once again the "Drawings
and Prints" department dominates the collection, with over 38,000 objects
acquired in 1963 alone.  This chart is interactive - click on a department 
name to remove it from the chart or double-click to isolate it and display
only its information.  (Scroll down for more department names.)

Note that the "Robert Lehman Collection" was not included on this chart
since it is a private collection that was bequeathed in its entirety to the 
museum in 1969.
"""
acquisitions_by_decade_text = """
This is a cleaner representation of the acquisition data grouped by decade.  It 
shows how the acquisition proportions change over time - for instance, Greek 
and Roman Art represents the majority of art collected from the 1870s, but is a 
relatively small proportion after that until we reach the 2010s, when there is 
another surge.  
"""

highlights_text = """
The museum designates certain pieces of art in its collection as highlights, 
i.e., pieces that are particularly notable.  This includes artifacts such as Tiffany 
vases, Babylonian necklaces, and of course paintings such as this one: 
*The Dance Class*, by Edgar Degas. 


There are almost 3000 highlights, spanning thousands of years, and they come 
from all over the world.  The map to the right shows the locations of all of the 
museum's highlights.  Spin the globe to see where they come from!  You can find 
out how many highlights are from a given country by hovering over its marker.

"""

 
app.layout = html.Div([
    #Opening part
    html.H1('Visualizations from the Metropolitan Museum of Art', style={'textAlign': 'center', 'margin': '0px'}),
    html.Div([dcc.Markdown(opening_text)], style={'margin':'2em'}),
    
    # 100 years of collections     
    html.Div([
        html.H2('100 Years of Collections',),
        html.Hr(style={'height':'5px', 'border-width':'0', 'background-color': '#00A4BD'}),

        html.Div([   
            html.H3('1923', style={'textAlign': 'center'}),
            dcc.Graph(id='objects-vs-depts-1923', figure = fig2),], 
            style={'width': '49%', 'display': 'inline-block', 'padding': '0 50', },),

        html.Div([
            html.H3('2023', style={'textAlign': 'center'}),
            dcc.Graph(id='objects-vs-depts-2023', figure = fig1)], 
            style={'width': '49%', 'display': 'inline-block', 'padding': '0 20', 'float': 'right'}),
        
        html.P(),
        html.Div([dcc.Markdown(collections_text)]),
        ], style={'margin':'2em'}),

  # Acquisitions Over Time  
    html.Div([
        html.H2('Acquisitions Over Time',),
        html.Hr(style={'height':'5px', 'border-width':'0', 'background-color': '#00A4BD'}),

        dcc.Graph(
            id='objects-by-dept-by-year',
            figure = fig3),
        
        html.P(),
        html.Div([dcc.Markdown(acquisitions_over_time_text)]),
        ], style={'margin':'2em'}),

# Acquisitions by Decade
    html.Div([
        html.H2('Acquisitions by Decade',),
        html.Hr(style={'height':'5px', 'border-width':'0', 'background-color': '#00A4BD'}),
    
    html.Div([dcc.Markdown(acquisitions_by_decade_text)]),
        dcc.Graph(id='objects-by-dept-by-decade',
        figure = fig4
    )], style={'margin':'2em'}),

# Mapped Highlights
    html.Div([
        html.H2('Highlights of the Collection',),
        html.Hr(style={'height':'5px', 'border-width':'0', 'background-color': '#00A4BD'}),

        html.Div([
            html.Div([   
                html.Img(src=get_asset_url('degas_class_smaller.jpg'), 
                         alt="Picture of the painting The Dance Class by Edgar Degas", 
                         title="The Dance Class, Edgar Degas"),],
                style={'padding': '0 50'},
                ),

            html.Div([
                html.H3('Museum Highlights',style={'textAlign': 'center'}),
                dcc.Markdown(highlights_text)], 
                style={'margin': '0 2%'}
                ),

            html.Div([   
                dcc.Graph(id='geo-map-highlights', figure = fig5)],
               style={"border":"5px black solid", "height": "425", "width": "425", "margin": "0 0 5"}
                       ),
        ],style={'margin':'2em', 'display': 'flex'}),
    ]),
],style={"background-color": background_color, "font-family": "Serif", "margin": "0px"})

if __name__ == '__main__':
    app.run_server(debug=False, 
                   port='8050', 
                   dev_tools_ui=None, 
                   dev_tools_props_check=None, 
                   use_reloader=True, 
                   dev_tools_hot_reload=True,
                   dev_tools_hot_reload_interval='3',
                   dev_tools_hot_reload_max_retry='8',
                   dev_tools_hot_reload_watch_interval="0.5",
                   dev_tools_silence_routes_logging=True)
