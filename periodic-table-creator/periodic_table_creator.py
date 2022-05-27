# based on https://docs.bokeh.org/en/latest/docs/gallery/periodic.html

from io import StringIO
from multiprocessing.dummy import Semaphore
from PIL import Image
import pandas as pd
import streamlit as st
from bokeh.io import output_file, show, save, export_png
from bokeh.plotting import figure
from bokeh.palettes import all_palettes, Turbo256 
from bokeh.transform import dodge, factor_cmap
from bokeh.models import Title
from bokeh.core.properties import value


# must be called as first command
try:
    st.set_page_config(layout="wide")
except:
    st.beta_set_page_config(layout="wide")


st.sidebar.title('Crown Castle Map')

def determineStars(row):
    stars = '<div class="rating">'
    skills = [1, 2, 3, 4, 5, 6, 7, 8]
    for num in skills:
        if row['SME'] == num:
            stars = stars + '<span style="color:gold; font-size: 30px">★</span>'
        else:
            if row[f'SKILL {num}'] == 1:
                if row[f'jobskill{num}'] == 1:
                    stars = stars + '<span style="color:#8E9595; font-size: 26px">★</span>'
                else:
                    stars = stars + '<span style="color:#3E8E4B; font-size: 26px">★</span>'
            else:
                if row[f'jobskill{num}'] == 1:
                    stars = stars + '<span style="color:#ff636d; font-size: 26px">★</span>'
                else:
                    stars = stars + '<span style="color:#8E9595; font-size: 20px">☆</span>'
    return stars + "</div>"

def determineStarsVacancy(row, s=[1,1,1,1,1,1,1,1,1]):
    stars = '<div class="rating">'
    skills = [1, 2, 3, 4, 5, 6, 7, 8]
    for num in skills:
        if row['SME'] == num:
            stars = stars + '<span style="color:gold; font-size: 30px">★</span>'
        else:
            if row[f'SKILL {num}'] == 1:
                if s[num] == 1:
                    stars = stars + '<span style="color:#8E9595; font-size: 26px">★</span>'
                else:
                    stars = stars + '<span style="color:#3E8E4B; font-size: 26px">★</span>'
            else:
                if s[num] == 1:
                    stars = stars + '<span style="color:#ff636d; font-size: 26px">★</span>'
                else:
                    stars = stars + '<span style="color:#8E9595; font-size: 20px">☆</span>'
    return stars + "</div>"

def determineGaps(row):
    gap = 0
    skills = [1, 2, 3, 4, 5, 6, 7, 8]
    for num in skills:
        if row[f'SKILL {num}'] == 1:
            if row[f'jobskill{num}'] == 1:
                gap = gap + 0
            else:
                gap = gap + 1
        else:
            if row[f'jobskill{num}'] == 1:
                gap = gap - 1
            else:
                gap = gap + 0
    return gap

def determineGapsVacancy(row, s=[1,1,1,1,1,1,1,1,1]):
    gap = 0
    skills = [1, 2, 3, 4, 5, 6, 7, 8]
    for num in skills:
        if row[f'SKILL {num}'] == 1:
            if s[num] == 1:
                gap = gap + 0
            else:
                gap = gap + 1
        else:
            if s[num] == 1:
                gap = gap - 1
            else:
                gap = gap + 0
    return gap

def determineGapColor(row):
    color=""
    if row['gapscore'] > 0:
        color='#4da3f7'
    if row['gapscore'] == 0:
        color='#92c6f7'
    if row['gapscore'] < 0:
        color='#d6ebff'
    return color


def determineOutcomeColor(row):
    color=""
    if row['outcomespercentage'] >= 95:
        color='#56ad63'
    if row['outcomespercentage'] > 90:
        color='#87cd92'
    if row['outcomespercentage'] > 80:
        color='#b3e0ba'
    if row['outcomespercentage'] > 70:
        color='#d8ecbd'
    if row['outcomespercentage'] >= 0:
        color='#edfcef'
    return color


def try_expander(expander_name, sidebar=True):
    if sidebar:
        try:
            return st.sidebar.expander(expander_name)
        except:
            return st.sidebar.beta_expander(expander_name)
    else:
        try:
            return st.expander(expander_name)
        except:
            return st.beta_expander(expander_name)


# load data

df = pd.read_csv("mapdataformatted.csv", header=0, encoding='utf-8')
df['skillsdisplay'] = df.apply (lambda row: determineStars(row), axis=1)
df['gapscore'] = df.apply (lambda row: determineGaps(row), axis=1)
df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
# edit data
df["lastName"] = df["lastName"].str.replace('\\n', '\n', regex=False)
df["groupname"] = df["groupname"].str.replace('\\n', ' ', regex=False)

df_group = pd.pivot_table(df, values='atomicnumber', index=['group','groupname'], 
    columns=[], aggfunc=pd.Series.nunique).reset_index()
df["color"] = df["color"].fillna('')

periods = [str(x) for x in set(df.period.values.tolist())]
periods_bottomrow = str(len(periods)+1)
periods += [periods_bottomrow]
df["period"] = [periods[x-1] for x in df.period]

groups = [str(x) for x in df_group.group]
groupnames = [str(x) for x in df_group.groupname]


# plot config options in sidebar
with try_expander('Fill Vacancy'):
    vacancy = st.selectbox(
     'Vacancy',
     ('None','T:1,R:B,L:1','T:1,R:B,L:2', 'T:2,R:B,L:2', 'T:3,R:A,L:1', 'T:3,R:B,L:1'))
    if vacancy == 'T:1,R:B,L:1':
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, [0,0,1,0,0,0,0,0,0]), axis=1)
        df['skillsdisplay'] = df.apply (lambda row: determineStarsVacancy(row, [0,0,1,0,0,0,0,0,0]), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'T:1,R:B,L:2':
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, [0,0,1,1,0,0,0,0,0]), axis=1)
        df['skillsdisplay'] = df.apply (lambda row: determineStarsVacancy(row, [0,0,1,1,0,0,0,0,0]), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'T:3,R:A,L:1':
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, [0,1,1,1,0,0,0,0,0]), axis=1)
        df['skillsdisplay'] = df.apply (lambda row: determineStarsVacancy(row, [0,1,1,1,0,0,0,0,0]), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'None':
        df['gapscore'] = df.apply (lambda row: determineGaps(row), axis=1)
        df['skillsdisplay'] = df.apply (lambda row: determineStars(row), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)

plot_title = ''
plot_font = 'Helvetica'

with try_expander('Color'):
    color = st.selectbox('Color Gradient', ['Gap Score'], index=0)
    if color == 'Outcome Percentage':
        df['color'] = df.apply (lambda row: determineOutcomeColor(row), axis=1)


with try_expander('Format'):
    plot_scale = st.slider('OVERALL SCALE', min_value=50, max_value=300, value=100, step=5, format='%d%%')/100.00
    
    plot_width = round(len(groups) * 100 * plot_scale)
    plot_width = st.slider('Plot width', min_value=500, max_value=3000, value=1600, step=100, format='%dpx')
    
    plot_height = round(len(periods) * 100 * plot_scale)
    plot_height = st.slider('Plot height', min_value=300, max_value=2000, value=1120, step=20, format='%dpx')

    title_size = round(48 * plot_scale)
    title_size = str(st.slider('Title', min_value=5, max_value=72, value=title_size, step=1, format='%dpx')) + 'px'
    
    element_number_size = round(11 * plot_scale)
    element_number_size = str(st.slider('Atomic Number', min_value=5, max_value=72, value=element_number_size, step=1, format='%dpx')) + 'px'
    
    element_firstName_size = 17
    element_firstName_size = str(st.slider('firstName', min_value=5, max_value=72, value=element_firstName_size, step=1, format='%dpx')) + 'px'
    
    element_name_size = round(11 * plot_scale)
    element_name_size = str(st.slider('Full name', min_value=5, max_value=72, value=element_name_size, step=1, format='%dpx')) + 'px'
    
    group_name_size = round(12 * plot_scale)
    group_name_size = str(st.slider('Group', min_value=5, max_value=72, value=group_name_size, step=1, format='%dpx')) + 'px'
    
    trademark_size = round(12 * plot_scale)
    trademark_size = str(st.slider('Trademark', min_value=5, max_value=72, value=trademark_size, step=1, format='%dpx')) + 'px'

    text_line_height = 0.6 if plot_scale <= 0.9 else 0.7 if plot_scale <=1.1 else 0.8 if plot_scale < 1.5 else 0.9
    text_line_height = st.slider('Text line height', min_value=0.5, max_value=1.5, value=text_line_height, step=0.1, format='%f')

    border_line_width = 2
    border_line_width = st.slider('Border line width', min_value=0, max_value=10, value=border_line_width, step=1, format='%dpx')
    element_color = st.selectbox('Element Color', ['From datafile','Category20','Category20b','Category20c'], index=0)
    title_color = st.color_picker('Title color', '#3B3838')
    text_color = st.color_picker('Element Text color', '#3B3838')
    groupname_color = st.color_picker('Groupname color', '#757171')
    trademark_color = st.color_picker('Trademark color', '#757171')

    if element_color.startswith('Category20'):
        colors = all_palettes[element_color][len(groups)+2]
        df["color"] = df.apply(lambda x: colors[x['group']-1], axis=1)

    df["group"] = df["group"].astype(str)

with try_expander('Filter'):
    skills = st.multiselect(
     'Skills',
     [1, 2, 3, 4, 5, 6, 7, 8],
     [])
    sme = st.multiselect(
    'SME',
    [1, 2, 3, 4, 5, 6, 7, 8],
    [])
    outcomes = st.slider('Positive outcome percentage >', 0, 100, 0)
    team = st.multiselect(
     'Team',
     [1, 2, 3, 4],
     [1, 2, 3, 4])

    if len(sme) > 0:
        df = df[df['SME'].isin(sme)]
    if len(team) > 0:
        df = df[df['team'].isin(team)]
    if len(skills) > 0:
        for num in skills:
            df = df[df[f'SKILL {num}'] == 1]
    if outcomes != 0:
        df = df[df['outcomespercentage'] > outcomes]

with try_expander('Find Gaps'):
    qualifications = st.selectbox(
     'Qualifications',
     ("All","Underqualified", "Qualified", "Overqualified"))
    gaps = st.slider('Gap Score', -9, 8, -9)
    if "Underqualified" == qualifications:
        df = df[df['gapscore'] < 0]
    if "Qualified" == qualifications:
        df = df[df['gapscore'] == 0]
    if "Overqualified" == qualifications:
        df = df[df['gapscore'] > 0]
    if gaps != -9:
        df = df[df['gapscore'] >= gaps]

with try_expander('Key'):
    st.markdown('''Sort by skills. Sort by outcome percentage.''')




# define figure
TOOLTIPS = """
    <div style="width:300px; padding:10px;background-color: white;">
        <div>
            <span style="font-size: 30px; font-weight: bold;">@firstName @lastName</span>
        </div>
        <div>
            <span style="font-size: 14px; font-weight: bold; ">@groupname Level: @level</span>
        </div>
        <br>
        <div>
            <span style="font-size: 20px; font-weight: bold; margin-bottom:20px">Outcome: @Outcomes Scope: @Scope Outcomes Success: @outcomespercentage %</span>
        </div>
        <br>
        @skillsdisplay
        <div>
        </div>
"""



p = figure(plot_width=plot_width, plot_height=plot_height,
    x_range=groups,
    y_range=list(reversed(periods)),
    tools="hover",
    toolbar_location="below",
    toolbar_sticky=False,
    tooltips=TOOLTIPS)

r = p.rect("group", "period", 0.94, 0.94, 
    source=df,
    fill_alpha=0.7, 
    color="color", 
    line_width=border_line_width)

text_props = {"source": df, "text_baseline":"middle", "text_color":text_color}

# print number
p.text(x=dodge("group", -0.4, range=p.x_range), 
    y=dodge("period", 0.3, range=p.y_range),
    text="atomicnumber",
    text_align="left",
    text_font=value(plot_font),
    text_font_style="italic",
    text_font_size=element_number_size,
    **text_props)

p.text(x=dodge("group", -0.4, range=p.x_range), 
    y=dodge("period", 0.3, range=p.y_range),
    text='''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="600" height="600" fill="white">

  <title>Abstract user icon</title>

  <defs>
    <clipPath id="circular-border">
      <circle cx="300" cy="300" r="280"/>
    </clipPath>
    <clipPath id="avoid-antialiasing-bugs">
	  <rect width="100%" height="498"/>
    </clipPath>
  </defs>
  
  <circle cx="300" cy="300" r="280" fill="black" clip-path="url(#avoid-antialiasing-bugs)"/>
  <circle cx="300" cy="230" r="115"/>
  <circle cx="300" cy="550" r="205" clip-path="url(#circular-border)"/>
</svg>''',
    text_align="left",
    text_font=value(plot_font),
    text_font_style="italic",
    text_font_size=element_number_size,
    **text_props)


# print firstName
p.text(x=dodge("group", -0.2, range=p.x_range),
    y=dodge("period", 0.1, range=p.y_range),
    text="firstName",
    text_font=value(plot_font),
    text_font_style="bold",
    text_font_size=element_firstName_size,
    **text_props)

# print element name
p.text(x=dodge("group", 0, range=p.x_range),
    y=dodge("period", -0.25, range=p.y_range),
    text="lastName",
    text_align="center",
    text_line_height=text_line_height,
    text_font=value(plot_font),
    text_font_size=element_name_size,
    **text_props)

# print title
p.add_layout(Title(text=plot_title,
    align="center",
    vertical_align="middle",
    text_line_height=1.5,
    text_color=title_color,
    text_font=plot_font,
    text_font_style="bold",
    text_font_size=title_size
    ), "above")

# print groupnames on x-axis
p.text(x=groups,
    y=[periods_bottomrow for x in groups],
    text=[x.replace(u' ', u'\n') for x in groupnames],
    text_align="center", 
    text_line_height=text_line_height,
    text_baseline="middle",
    text_font=value(plot_font),
    text_font_size=group_name_size,
    text_color=groupname_color
    )


p.outline_line_color = None
p.grid.grid_line_color = None
p.axis.visible = False
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.axis.major_label_standoff = 0
p.hover.renderers = [r] # only hover element boxes

# Set autohide to true to only show the toolbar when mouse is over plot
p.toolbar.autohide = True

st.header('Team Members: ')

st.bokeh_chart(p)

st.header('Fill Vacancies: ')

st.header('Promote: ')

with try_expander('Load Content', False):
    if st.checkbox('Upload your CSV', value=False):
        st.markdown('Upload your own Periodic Table CSV. Follow the example-format of "Edit CSV text" (utf-8 encoding, semicolon seperator, csv file-extension)')
        uploaded_file = st.file_uploader('Upload your CSV file', type=['csv'], accept_multiple_files=False)
    else:
        uploaded_file = None

    if uploaded_file is not None:
        bytes_data = uploaded_file.read().decode("utf-8", "strict") 
    else:
        try:
            with open('periodic-table-creator/periodic_nlp.csv', 'r') as f:
                bytes_data = f.read()
        except:
            with open('periodic_nlp.csv', 'r') as f:
                bytes_data = f.read()
        
    if st.checkbox('Edit CSV text', value=False):
        bytes_data = st.text_area('CSV file', value=bytes_data, height=200, max_chars=100000)

    data = StringIO(bytes_data)

    if st.checkbox('Show CSV data', value=False):
        st.table(df)



