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
import streamlit.components.v1 as components



# must be called as first command
try:
    st.set_page_config(layout="wide")
except:
    st.beta_set_page_config(layout="wide")


st.sidebar.title('Crown Castle Map')

def determineStars(row):
    stars = '<div class="rating">'
    skills = ["Innovation", "Agility", "Judgement", "Influence", "Collaboration", "Results", "Economics"]
    for s in skills:
        if row[s] >= 1:
            if row[s] >= 1:
                stars = stars + '<span style="color:#8E9595; font-size: 26px">★</span>'
            else:
                stars = stars + '<span style="color:#3E8E4B; font-size: 26px">★</span>'
        else:
            if row[f'js{s}'] >= 1:
                stars = stars + '<span style="color:#ff636d; font-size: 26px">★</span>'
            else:
                stars = stars + '<span style="color:#8E9595; font-size: 20px">☆</span>'
    return stars + "</div>"

def determineSkillsDisplay(row, s):
    stars = ''
    isRequired = row[f'js{s}'] > 0
    hasSkill = row[s] > 0
    if isRequired: 
        diff = row[s] - row[f'js{s}']
        if diff == 0:
            stars = "☑" * row[s]
        if diff < 0:
            have = "☑" * row[s]
            missing = "☒" * abs(diff)
            stars = have + missing
        if diff > 0:
            have = "☑" * row[s]
            extra = "★" * diff
            stars = have + extra

    else:
        if not hasSkill:
            stars = "☒" * row[f'js{s}']
        else:
            stars = "★" * row[s]

    if row['firstName'] == "VACANT":
        stars = "□" * row[f'js{s}']
            
    return stars

def determineSkillsDisplayVacancy(row, s, values):
    stars = ''
    isRequired = values[s] > 0
    hasSkill = row[s] > 0
    if isRequired: 
        diff = row[s] - values[s]
        if diff == 0:
            stars = "☑" * row[s]
        if diff < 0:
            have = "☑" * row[s]
            missing = "☒" * abs(diff)
            stars = have + missing
        if diff > 0:
            have = "☑" * row[s]
            extra = "★" * diff
            stars = have + extra

    else:
        if not hasSkill:
            stars = "☒" * values[s]
        else:
            stars = "★" * row[s]
            
    return stars

def setSkillsDisplay(allskills, Vacancy=False, values={}):
    if Vacancy:
        for s in allskills:
            df[f'dsply{s}'] = df.apply (lambda row: determineSkillsDisplayVacancy(row, s, values), axis=1)
    else:
        for s in allskills:
            df[f'dsply{s}'] = df.apply (lambda row: determineSkillsDisplay(row, s), axis=1)


    

def determineGaps(row):
    gap = 0
    surplus = 0
    skills = ["Innovation", "Agility", "Judgement", "Influence", "Collaboration", "Results", "Economics"]
    for s in skills:
        if row[s] >= 1:
            if row[f'js{s}'] >= 1:
                gap = row[s] - row[f'js{s}']
            else:
                surplus = surplus + row[s]
        else:
            if row[f'js{s}'] >= 1:
                gap = gap - row[f'js{s}']
        if gap > 0:
            gap = gap + surplus
    return gap

def determineGapsVacancy(row, values):
    gap = 0
    surplus = 0
    skills = ["Innovation", "Agility", "Judgement", "Influence", "Collaboration", "Results", "Economics"]
    for s in skills:
        if row[s] >= 1:
            if values[s] >= 1:
                gap = row[s] - values[s]
            else:
                surplus = surplus + row[s]
        else:
            if values[s] >= 1:
                gap = gap - values[s]
        if gap > 0:
            gap = gap + surplus
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
    elif row['outcomespercentage'] > 90:
        color='#87cd92'
    elif row['outcomespercentage'] > 80:
        color='#b3e0ba'
    elif row['outcomespercentage'] > 70:
        color='#d8ecbd'
    elif row['outcomespercentage'] >= 0:
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
allskills = ["Innovation", "Agility", "Judgement", "Influence", "Collaboration", "Results", "Economics"]
df = pd.read_csv("mapdata2.csv", header=0, encoding='utf-8')
df['skillsdisplay'] = df.apply (lambda row: determineStars(row), axis=1)
df['gapscore'] = df.apply (lambda row: determineGaps(row), axis=1)
df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
setSkillsDisplay(allskills)

# edit data
df["lastName"] = df["lastName"].str.replace('\\n', '\n', regex=False)
df["team"] = df["team"].str.replace('\\n', ' ', regex=False)

df_group = pd.pivot_table(df, values='level', index=['group','team'], 
    columns=[], aggfunc=pd.Series.nunique).reset_index()
df["color"] = df["color"].fillna('')

periods = [str(x) for x in set(df.period.values.tolist())]
periods_bottomrow = str(len(periods)+1)
periods += [periods_bottomrow]
df["period"] = [periods[x-1] for x in df.period]

groups = [str(x) for x in df_group.group]
teams = [str(x) for x in df_group.team]

with try_expander('Filter'):
    skills = st.multiselect(
     'Skills',
     allskills,
     allskills)
    skillLevel = st.slider('Skill level', 0, 4, 0)
    outcomes = st.slider('Positive outcome percentage >', 0, 100, 0)
    team = st.multiselect(
     'Team',
     ["Corp", "TA", "Learning","Learning Con't", "Immersion","Immersion Con't","Coaching"],
     ["Corp", "TA", "Learning","Learning Con't", "Immersion","Immersion Con't","Coaching"])

    if len(team) > 0:
        df = df[df['team'].isin(team)]
    if len(skills) > 0:
        for s in skills:
            df = df[df[s] >= skillLevel]
    if outcomes != 0:
        df = df[df['outcomespercentage'] > outcomes]

with try_expander('Find Gaps'):
    qualifications = st.selectbox(
     'Qualifications',
     ("All","Underqualified", "Qualified", "Overqualified"))
    if "Underqualified" == qualifications:
        df = df[df['gapscore'] < 0]
    if "Qualified" == qualifications:
        df = df[df['gapscore'] == 0]
    if "Overqualified" == qualifications:
        df = df[df['gapscore'] > 0]



# plot config options in sidebar
with try_expander('Fill Vacancy'):
    val1 = {"Innovation": 0, "Agility": 1,"Judgement": 0, "Influence": 0, "Collaboration": 1, "Results": 1, "Economics": 1}
    val2 = {"Innovation": 0, "Agility": 1,"Judgement": 0, "Influence": 0, "Collaboration": 1, "Results": 1, "Economics": 1}
    val3 = {"Innovation": 1, "Agility": 1,"Judgement": 1, "Influence": 1, "Collaboration": 1, "Results": 1, "Economics": 1}
    val4 = {"Innovation": 1, "Agility": 1,"Judgement": 1, "Influence": 1, "Collaboration": 1, "Results": 1, "Economics": 1}
    val5 = {"Innovation": 1, "Agility": 1,"Judgement": 1, "Influence": 1, "Collaboration": 1, "Results": 1, "Economics": 1}
    vacancy = st.selectbox(
     'Vacancy',
     ('None','TA | Level 1','Learning | Level: 1', 'Immersion | Level: 1A', 'Immersion | Level: 1B', 'Immersion | Level: 1C'))
    if vacancy == 'TA | Level 1':
        setSkillsDisplay(allskills, True, val1)
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, val1), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'Learning | Level: 1':
        setSkillsDisplay(allskills, True, val2)
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, val2), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'Immersion | Level: 1A':
        setSkillsDisplay(allskills, True, val3)
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, val3), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'Immersion | Level: 1B':
        setSkillsDisplay(allskills, True, val4)
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, val4), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'Immersion | Level: 1C':
        setSkillsDisplay(allskills, True, val5)
        df['gapscore'] = df.apply (lambda row: determineGapsVacancy(row, val5), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)
    if vacancy == 'None':
        setSkillsDisplay(allskills)
        df['gapscore'] = df.apply (lambda row: determineGaps(row), axis=1)
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)

plot_title = ''
plot_font = 'Helvetica'

with try_expander('Color'):
    color = st.selectbox('Color Gradient', ['Gap Score', 'Outcome Percentage'], index=0)
    if color == 'Outcome Percentage':
        df['color'] = df.apply (lambda row: determineOutcomeColor(row), axis=1)
    if color == 'Gap Score':
        df['color'] = df.apply (lambda row: determineGapColor(row), axis=1)

with try_expander('Format'):
    plot_scale = st.slider('OVERALL SCALE', min_value=50, max_value=300, value=100, step=5, format='%d%%')/100.00
    
    plot_width = round(len(groups) * 100 * plot_scale)
    plot_width = st.slider('Plot width', min_value=500, max_value=3000, value=950, step=100, format='%dpx')
    
    plot_height = round(len(periods) * 100 * plot_scale)
    plot_height = st.slider('Plot height', min_value=300, max_value=2000, value=940, step=20, format='%dpx')

    title_size = round(48 * plot_scale)
    title_size = str(st.slider('Title', min_value=5, max_value=72, value=title_size, step=1, format='%dpx')) + 'px'
    
    element_number_size = round(11 * plot_scale)
    element_number_size = str(st.slider('Level', min_value=5, max_value=72, value=element_number_size, step=1, format='%dpx')) + 'px'
    
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
    team_color = st.color_picker('team color', '#757171')
    trademark_color = st.color_picker('Trademark color', '#757171')

    if element_color.startswith('Category20'):
        colors = all_palettes[element_color][len(groups)+2]
        df["color"] = df.apply(lambda x: colors[x['group']-1], axis=1)

    df["group"] = df["group"].astype(str)




# define figure
TOOLTIPS = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
    <div style="width:300px; padding:10px;background-color: white;">
        <div>
            <span style="font-size: 30px; font-weight: bold;">@firstName @lastName @role</span>
        </div>
        <div>
            <span style="font-size: 14px; font-weight: bold; ">@team level: @level</span>
        </div>
                <div>
            <span style="font-size: 14px; font-weight: bold; ">Gap Score: @gapscore</span>
        </div>
        <br>
        <div>
            <span style="font-size: 20px; font-weight: bold; margin-bottom:20px">Outcome: @Outcomes Scope: @Scope Outcomes Success: @outcomespercentage %</span>
        </div>
        <div>
            <span style="font-size: 20px; font-weight: bold; margin-bottom:20px">
            Innovation @Innovation/@jsInnovation : @dsplyInnovation <br>
            Agility @Agility/@jsAgility : @dsplyAgility <br>
            Judgement @Judgement/@jsJudgement : @dsplyJudgement  <br>
            Influence @Influence/@jsInfluence : @dsplyInfluence <br>
            Collaboration @Collaboration/@jsCollaboration : @dsplyCollaboration <br>
            Results @Results/@jsResults : @dsplyResults <br>
            Economics @Economics/@jsEconomics : @dsplyEconomics  <br>
            </span>
        </div>
        <br>
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
    text="level",
    text_align="left",
    text_font=value(plot_font),
    text_font_style="italic",
    text_font_size=element_number_size,
    **text_props)

# p.text(x=dodge("group", -0.4, range=p.x_range), 
#     y=dodge("period", 0.3, range=p.y_range),
#     text='''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="600" height="600" fill="white">

#   <title>Abstract user icon</title>

#   <defs>
#     <clipPath id="circular-border">
#       <circle cx="300" cy="300" r="280"/>
#     </clipPath>
#     <clipPath id="avoid-antialiasing-bugs">
# 	  <rect width="100%" height="498"/>
#     </clipPath>
#   </defs>
  
#   <circle cx="300" cy="300" r="280" fill="black" clip-path="url(#avoid-antialiasing-bugs)"/>
#   <circle cx="300" cy="230" r="115"/>
#   <circle cx="300" cy="550" r="205" clip-path="url(#circular-border)"/>
# </svg>''',
#     text_align="left",
#     text_font=value(plot_font),
#     text_font_style="italic",
#     text_font_size=element_number_size,
#     **text_props)


# print firstName
p.text(x=dodge("group", 0, range=p.x_range),
    y=dodge("period", 0.1, range=p.y_range),
    text="firstName",
    text_font=value(plot_font),
    text_align="center",
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

# print teams on x-axis
p.text(x=groups,
    y=[periods_bottomrow for x in groups],
    text=[x.replace(u' ', u'\n') for x in teams],
    text_align="center", 
    text_line_height=text_line_height,
    text_baseline="middle",
    text_font=value(plot_font),
    text_font_size=group_name_size,
    text_color=team_color
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
st.text('  ')

st.bokeh_chart(p)

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



