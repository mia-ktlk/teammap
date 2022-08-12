# based on https://docs.bokeh.org/en/latest/docs/gallery/periodic.html

from io import StringIO
from multiprocessing.dummy import Semaphore
import numpy as np
from PIL import Image
import pandas as pd
import streamlit as st
from bokeh.io import output_file, show, save, export_png
from bokeh.plotting import figure
from bokeh.palettes import all_palettes, Turbo256
from bokeh.transform import dodge, factor_cmap
from bokeh.models import Title
from bokeh.core.properties import value
import global_vars

# must be called as first command
try:
    st.set_page_config(layout="wide")
except:
    st.beta_set_page_config(layout="wide")

st.sidebar.title('Crown Castle Map')
allskills = ["Innovation", "Influence", "Savvy", "Craft Skill 1", "Craft Skill 2", "Craft Skill 3", "Craft Skill 4",
             "Craft Skill 5", "Craft Skill 6", "Craft Skill 7", "Craft Skill 8", "Craft Skill 9", "Craft Skill 10",
             "Craft Skill 11", "Craft Skill 12", "Craft Skill 13", "Craft Skill 14", "Craft Skill 15", "Craft Skill 16",
             "Craft Skill 17", "Craft Skill 18", "Craft Skill 19", "Craft Skill 20", "Craft Skill 21", "Craft Skill 22",
             "Craft Skill 23", "Craft Skill 24", "Craft Skill 25", "Craft Skill 26", "Craft Skill 27", "Craft Skill 28",
             "Craft Skill 29", "Craft Skill 30", "Craft Skill 31", "Craft Skill 32", "Craft Skill 33", "Craft Skill 34",
             "Craft Skill 35", "Craft Skill 36", "Craft Skill 37", "Craft Skill 38", "Craft Skill 39", "Craft Skill 40"]
display_skills = ["Innovation", "Influence", "Savvy", "CraftCount"]

position_attr = ["Unit","Group","Team","Role","Level","Period","Outcomes",'jsCraftCount']
for s in allskills:
    position_attr.append(f'js{s}')


def determineGroup(unit):
    if unit == "Talent":
        return 1
    elif unit == "Corp":
        return 2
    elif unit == "Engineering":
        return 3
    elif unit == "Sales":
        return 4
    elif unit == "Marketing":
        return 5
    elif unit == "Manufacturing":
        return 6


def determinePeriod(unit):
    ind = dups_units[dups_units['Unit'] == unit].index
    per = int(dups_units.loc[ind, 'count'].values)
    dups_units.loc[ind, 'count'] = per -1
    return per


def determineCraftCount(craft_skills, compare=False):
    total = 0
    if not compare:
        for skill in allskills:
            if craft_skills[f'js{skill}'] > 1:
                total += 1
    else:
        for skill in allskills:
            if craft_skills[f'js{skill}'] > 1:
                if craft_skills[skill] > 1:
                    total += 1

    return total


def determineVacancyCraftCount(craft_skills, pass_val, compare=False):
    total = 0
    if not compare:
        for skill in allskills:
            if pass_val[f'js{skill}'] > 1:
                total += 1
    else:
        for skill in allskills:
            if pass_val[f'js{skill}'] > 1:
                if craft_skills[skill] > 1:
                    total += 1

    return total


def determineStars(row):
    stars = '<div class="rating">'
    for s in display_skills:
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

    if row['Name'] == "VACANT":
        stars = "□" * row[f'js{s}']
    return stars


def determineSkillsDisplayVacancy(row, s, values):
    stars = ''
    isRequired = values[f'js{s}'] > 0
    hasSkill = row[s] > 0
    if isRequired:
        diff = row[s] - values[f'js{s}']
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
            stars = "☒" * values[f'js{s}']
        else:
            stars = "★" * row[s]

    return stars


def setSkillsDisplay(allskills, Vacancy=False, values={}):
    if Vacancy:
        for s in display_skills:
            if df.size > 0:
                df[f'dsply{s}'] = df.apply(lambda row: determineSkillsDisplayVacancy(row, s, values), axis=1)
    else:
        for s in display_skills:
            if df.size > 0:
                df[f'dsply{s}'] = df.apply(lambda row: determineSkillsDisplay(row, s), axis=1)


def determineGaps(row):
    gap = 0
    general_skills = allskills[0:3]
    craft_skills = allskills[3:]
    for sk in general_skills:
        skill_gap = row[sk] - row[f'js{sk}']
        gap += skill_gap

    for sk in craft_skills:
        # Only check craft skills if in the job requirements
        if row[f'js{sk}'] > 0:
            skill_gap = row[sk] - row[f'js{sk}']
        else:
            skill_gap = 0
        gap += skill_gap
    return gap


def determineGapsVacancy(row, values):
    gap = 0
    general_skills = allskills[0:3]
    craft_skills = allskills[3:]
    for sk in general_skills:
        skill_gap = row[sk] - values[f'js{sk}']
        gap += skill_gap

    for sk in craft_skills:
        # Only check craft skills if in the job requirements
        if values[f'js{s}'] > 0:
            skill_gap = row[sk] - values[f'js{sk}']
        else:
            skill_gap = 0
        gap += skill_gap
    return gap


def determineGapColor(row):
    color = ""
    if row['gapscore'] > 0:
        color = '#4da3f7'
    if row['gapscore'] == 0:
        color = '#92c6f7'
    if row['gapscore'] < 0:
        color = '#d6ebff'
    return color


def determineOutcomeColor(row):
    color = ""
    if row['OutcomePercent'] >= 95:
        color = '#56ad63'
    elif row['OutcomePercent'] > 90:
        color = '#87cd92'
    elif row['OutcomePercent'] > 80:
        color = '#b3e0ba'
    elif row['OutcomePercent'] > 70:
        color = '#d8ecbd'
    elif row['OutcomePercent'] >= 0:
        color = '#edfcef'
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


# load data (if any) from global state
df = global_vars.global_df

# See if the CSV has already been loaded once, if so prevent it from overwriting the new changes
if global_vars.data_loaded == 0:
    df = pd.read_csv("https://raw.githubusercontent.com/mia-ktlk/teammap/main/periodic-table-creator/newdata.csv", header=0, encoding='utf-8')
    global_vars.global_df = df
    global_vars.data_loaded += 1
if df.size > 0:
    for s in allskills:
        df[s].replace(np.NAN, 0, inplace=True)
    df[allskills] = df[allskills].applymap(np.int64)

    df['Group'] = df.apply(lambda row: determineGroup(row['Unit']), axis=1)
    dups_units = df.groupby(['Unit']).size().reset_index(name='count')


    # Reverse for better functionality with determinePeriod
    df = df[::-1]
    df['Period'] = df.apply(lambda row: determinePeriod(row['Unit']), axis=1)
    #Reverse again to return to proper order
    df = df[::-1]
    df['jsCraftCount'] = df.apply(lambda row: determineCraftCount(row),axis=1)
    df['CraftCount'] = df.apply(lambda row: determineCraftCount(row, True), axis=1)

    # determineStars occasionally throws error 'missing positional argument 'func' but a restart usually fixes it,
    # may need to change from passing DataFrames through lambda (not sure backend reason why)
    # seems to only occur when refreshing the page without doing any position swaps?????
    df['skillsdisplay'] = df.apply(lambda row: determineStars(row), axis=1)
    df['gapscore'] = df.apply(lambda row: determineGaps(row), axis=1)
    df['color'] = df.apply(lambda row: determineGapColor(row), axis=1)
    setSkillsDisplay(allskills)

    # edit data
    df["Name"] = df["Name"].str.replace('\\n', '\n', regex=False)
    df["Team"] = df["Team"].str.replace('\\n', ' ', regex=False)

    df_group = pd.pivot_table(df, values='Level', index=['Unit', 'Group'],
                              columns=[], aggfunc=pd.Series.nunique).reset_index()
    df["color"] = df["color"].fillna('')

    df.Period = pd.to_numeric(df.Period)
    Periods = [str(x) for x in set(df.Period.values.tolist())]
    Periods_bottomrow = str(len(Periods) + 1)
    Periods += [Periods_bottomrow]
    df["Period"] = [Periods[x-1] for x in df.Period]

    global_vars.global_df = df

    groups = [str(x) for x in df_group.Unit]
    Group = [str(x) for x in df_group.Group]

with try_expander('Filter'):
    skills = st.multiselect(
        'Skills',
        allskills,
        [])
    skillLevel = st.slider('Skill level', 0, 4, 0)
    outcomes = st.slider('Positive outcome percentage >', 0, 100, 0)
    team = st.multiselect(
        'Team',
        ["Corp", "TA", "Talent", "Learning", "Immersion", "Coaching", "Engineering", "Sales", "Marketing", "Manufacturing"],
        [])

    if len(team) > 0:
        try:
            df = df[df['Team'].isin(team)]
        except:
            print("Team Filter Failed to Set, may be no data points with set filters")
    if len(skills) > 0:
        for s in skills:
            try:
                df = df[df[s] >= skillLevel]
            except:
                print("Skill Filter Failed to Set, may be no data points with set filters")
    if outcomes != 0:
        try:
            df = df[df['OutcomePercent'] > outcomes]
        except:
            print("Outcome Filter Failed to Set, may be no data points with set filters")

with try_expander('Find Gaps'):
    qualifications = st.selectbox(
        'Qualifications',
        ("All", "Underqualified", "Qualified", "Overqualified"))
    if "Underqualified" == qualifications:
        df = df[df['gapscore'] < 0]
    if "Qualified" == qualifications:
        df = df[df['gapscore'] == 0]
    if "Overqualified" == qualifications:
        df = df[df['gapscore'] > 0]

# plot config options in sidebar




with try_expander('Fill Vacancy'):

    vacancy_dict= {
        "None": None
    }
    # Look up all Vacancies and gather as new DataFram
    vacancies = df.loc[df['Name'] == "VACANT", position_attr]

    # Iterate over the rows of new DF
    for index, row in vacancies.iterrows():
        # Make the key for Vacancy Dict the Team + Level + Role (ex: 'Learning | Level 2 - Designer')
        key = str(row['Team']) + " | Level" + str(row['Level']) + " - " + str(row['Role'])

        # For the score report for the row and insert in Dict
        result = row['jsInnovation': "jsCraft Skill 40"].to_dict()
        result['jsCraftCount'] = row['jsCraftCount']
        vacancy_dict[key] = result

    vacancy = st.selectbox(
        'Vacancy',
        vacancy_dict.keys())
    passVal = vacancy_dict.get(vacancy)
    if passVal is not None:
        if df.size > 0:
            df['gapscore'] = df.apply(lambda row: determineGapsVacancy(row, passVal), axis=1)
            df['jsCraftCount'] = df.apply(lambda row: determineVacancyCraftCount(row, passVal), axis=1)
            df['CraftCount'] = df.apply(lambda row: determineVacancyCraftCount(row, passVal, True), axis=1)
        setSkillsDisplay(allskills, True, passVal)

    else:
        if df.size > 0:
            df['gapscore'] = df.apply(lambda row: determineGaps(row), axis=1)
            df['jsCraftCount'] = df.apply(lambda row: determineCraftCount(row), axis=1)
            df['CraftCount'] = df.apply(lambda row: determineCraftCount(row, True), axis=1)
            setSkillsDisplay(allskills)
    if df.size > 0:
        df['color'] = df.apply(lambda row: determineGapColor(row), axis=1)


with try_expander('Swap Roles'):
    # Vacant Data Frame for Firing employee
    Employee_Cols = ["Name", "OutcomePercent"] + allskills
    vacant_vals = ["VACANT"]
    for s in Employee_Cols:
        if s == "Name":
            continue
        vacant_vals.append(0)
    vacant = pd.DataFrame(
        [vacant_vals],
        columns=Employee_Cols
    )
    vacant_series = vacant.squeeze()


    def swap():
        global df
        e1 = st.session_state.Emp1
        e2 = st.session_state.Emp2

        if df.size != global_vars.global_df.size:
            df = global_vars.global_df
        if e1 == e2:
            print("Can't swap same employee")
        elif e1 == "REMOVE EMPLOYEE":
            # Remove Employee 2 by making it a vacant slot
            e2_ind = df[(df['Name'] == e2.split(" | ")[0]) & (df['Role'] == e2.split(" | ")[1])].index.values[0]

            emp_2 = df.loc[e2_ind,
                   Employee_Cols]
            df.loc[e2_ind,
                   Employee_Cols] = vacant_series
            global_vars.df = df
        elif e2 == "REMOVE EMPLOYEE":
            # Remove Employee 1 by making it a vacant slot
            e1_ind = df[(df['Name'] == e1.split(" | ")[0]) & (df['Role'] == e1.split(" | ")[1])].index.values[0]

            emp_1 = df.loc[e1_ind,
                           Employee_Cols]

            df.loc[e1_ind,
                   Employee_Cols] = vacant_series
            global_vars.global_df = df
        else:
            # Swap the 2 employees jobs
            e1_ind = df[(df['Name'] == e1.split(" | ")[0]) & (df['Role'] == e1.split(" | ")[1])].index.values[0]
            e2_ind = df[(df['Name'] == e2.split(" | ")[0]) & (df['Role'] == e2.split(" | ")[1])].index.values[0]

            # Query for the job info for employee 1
            e1_job = df.loc[e1_ind,
                            position_attr]
            # Query for the job info for employee 2
            e2_job = df.loc[e2_ind,
                            position_attr]
            # Query for Employee 1, and assign to employee 2's job
            df.loc[e1_ind,
                   position_attr] = e2_job
            # Query for Employee 2, and assign to employee 1's job
            df.loc[e2_ind,
                   position_attr] = e1_job
            # Page refreshes after swap
            # Update global copy of the DataFrame to ensure it isn't wiped
            global_vars.global_df = df


    with st.form(key='my_form'):
        a = ["REMOVE EMPLOYEE"]
        for index, ro in df.iterrows():
            a.append(str(ro['Name']) + " | " + str(ro['Role']))

        employee1 = st.selectbox(
            "Employee 1",
            a, key='Emp1')

        employee2 = st.selectbox(
            "Employee 2",
            a, key='Emp2')
        st.form_submit_button(on_click=swap)

plot_title = ''
plot_font = 'Helvetica'

with try_expander('Color'):
    color = st.selectbox('Color Gradient', ['Gap Score', 'Outcome Percentage'], index=0)
    if color == 'Outcome Percentage':
        if df.size > 0:
            df['color'] = df.apply(lambda row: determineOutcomeColor(row), axis=1)
    if color == 'Gap Score':
        if df.size > 0:
            df['color'] = df.apply(lambda row: determineGapColor(row), axis=1)

with try_expander('Format'):
    plot_scale = st.slider('OVERALL SCALE', min_value=50, max_value=300, value=100, step=5, format='%d%%') / 100.00

    plot_width = round(len(groups) * 200 * plot_scale)
    plot_width = st.slider('Plot width', min_value=500, max_value=3000, value=950, step=100, format='%dpx')

    plot_height = round(len(Periods) * 100 * plot_scale)
    plot_height = st.slider('Plot height', min_value=300, max_value=2000, value=1500, step=20, format='%dpx')

    title_size = round(48 * plot_scale)
    title_size = str(st.slider('Title', min_value=5, max_value=72, value=title_size, step=1, format='%dpx')) + 'px'

    element_number_size = round(11 * plot_scale)
    element_number_size = str(
        st.slider('Level', min_value=5, max_value=72, value=element_number_size, step=1, format='%dpx')) + 'px'

    element_Name_size = 17
    element_Name_size = str(
        st.slider('Name', min_value=5, max_value=72, value=element_Name_size, step=1, format='%dpx')) + 'px'

    element_role_size = round(11 * plot_scale)
    element_role_size = str(
        st.slider('', min_value=5, max_value=72, value=element_role_size, step=1, format='%dpx')) + 'px'

    group_name_size = round(12 * plot_scale)
    group_name_size = str(
        st.slider('Unit', min_value=5, max_value=72, value=group_name_size, step=1, format='%dpx')) + 'px'

    trademark_size = round(12 * plot_scale)
    trademark_size = str(
        st.slider('Trademark', min_value=5, max_value=72, value=trademark_size, step=1, format='%dpx')) + 'px'

    text_line_height = 0.6 if plot_scale <= 0.9 else 0.7 if plot_scale <= 1.1 else 0.8 if plot_scale < 1.5 else 0.9
    text_line_height = st.slider('Text line height', min_value=0.5, max_value=1.5, value=text_line_height, step=0.1,
                                 format='%f')

    border_line_width = 2
    border_line_width = st.slider('Border line width', min_value=0, max_value=10, value=border_line_width, step=1,
                                  format='%dpx')
    element_color = st.selectbox('Element Color', ['From datafile', 'Category20', 'Category20b', 'Category20c'],
                                 index=0)
    title_color = st.color_picker('Title color', '#3B3838')
    text_color = st.color_picker('Element Text color', '#3B3838')
    team_color = st.color_picker('team color', '#757171')
    trademark_color = st.color_picker('Trademark color', '#757171')

    if element_color.startswith('Category20'):
        colors = all_palettes[element_color][len(groups) + 2]
        if df.size > 0:
            df["color"] = df.apply(lambda x: colors[x['Unit'] - 1], axis=1)

    df["Unit"] = df["Unit"].astype(str)

# define figure
TOOLTIPS = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
    <div style="width:300px; padding:10px;background-color: white;">
        <div>
            <span style="font-size: 18px; font-weight: bold;">@Name @Role</span>
        </div>
        <div>
            <span style="font-size: 14px; font-weight: bold; ">@Team Level: @Level</span>
        </div>
                <div>
            <span style="font-size: 14px; font-weight: bold; ">Gap Score: @gapscore</span>
        </div>
        <br>
        <div>
            <span style="font-size: 18px; font-weight: bold; margin-bottom:20px"> Outcomes Success: @OutcomePercent Outcome: @Outcomes%</span>
        </div>
        <div>
            <span style="font-size: 18px; font-weight: bold; margin-bottom:20px">
            Innovation @Innovation/@jsInnovation : @dsplyInnovation <br>
            Influence @Influence/@jsInfluence : @dsplyInfluence <br>
            Savvy @Savvy/@jsSavvy : @dsplySavvy  <br>
            CraftSkills @CraftCount/@jsCraftCount: @dsplyCraftCount
            </span>
        </div>
        <br>
        <div>
        </div>
"""

p = figure(plot_width=plot_width, plot_height=plot_height,
           x_range=groups,
           y_range=list(reversed(Periods)),
           tools="hover",
           toolbar_location="below",
           toolbar_sticky=False,
           tooltips=TOOLTIPS)

r = p.rect("Unit", "Period", 0.94, 0.94,
           source=df,
           fill_alpha=0.7,
           color="color",
           line_width=border_line_width)

text_props = {"source": df, "text_baseline": "middle", "text_color": text_color}

# print number
p.text(x=dodge("Unit", -0.4, range=p.x_range),
       y=dodge("Period", 0.3, range=p.y_range),
       text="Level",
       text_align="left",
       text_font=value(plot_font),
       text_font_style="italic",
       text_font_size=element_number_size,
       **text_props)

# print Name
p.text(x=dodge("Unit", 0, range=p.x_range),
       y=dodge("Period", 0.1, range=p.y_range),
       text="Name",
       text_font=value(plot_font),
       text_align="center",
       text_font_style="bold",
       text_font_size=element_Name_size,
       **text_props)

# print role
p.text(x=dodge("Unit", 0, range=p.x_range),
       y=dodge("Period", -0.25, range=p.y_range),
       text="Role",
       text_align="center",
       text_line_height=text_line_height,
       text_font=value(plot_font),
       text_font_size=element_role_size,
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
       y=[Periods_bottomrow for x in groups],
       text=[x.replace(u' ', u'\n') for x in groups],
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
p.hover.renderers = [r]  # only hover element boxes

# Set autohide to true to only show the toolbar when mouse is over plot
p.toolbar.autohide = True
st.header('Team Members: ')
st.text('  ')

st.bokeh_chart(p, use_container_width=True)

with try_expander('Load Content', False):
    if st.checkbox('Upload your CSV', value=False):
        st.markdown(
            'Upload your own Table CSV. Follow the example-format of "Edit CSV text" (utf-8 encoding, semicolon seperator, csv file-extension)')
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
