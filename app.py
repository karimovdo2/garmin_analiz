import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pyfonts import load_font

#---------------------------------------------------------------
#Configs and functions -----------------------------------------
st.set_page_config(
    page_title="Last Month in Sports",
    page_icon="weight_lifter",
    #layout="wide",
     )

#session states
if "init" not in st.session_state:
    st.session_state["init"] = True
    st.session_state["is_csv"] = None
    st.session_state["upload_success"] = None
    st.session_state["rerun_data_processing"] = True
    st.session_state["FormSubmitter:user_inputs-Create visualisation"]=None
#st.write(st.session_state)

def set_rerun_true():
    st.session_state["rerun_data_processing"] = True

def form_submit_callback():
    st.session_state["rerun_data_processing"] = False
    #st.session_state["run_visualisation"] = True

#cache data and fonts
@st.cache_data(persist=True, show_spinner=False)
def load_fonts():
    font_b = load_font(
                    font_url='https://github.com/andrew-paglinawan/QuicksandFamily/blob/master/fonts/statics/Quicksand-Bold.ttf?raw=true'
                    )
    font_r = load_font(
                    font_url='https://github.com/andrew-paglinawan/QuicksandFamily/blob/master/fonts/statics/Quicksand-Regular.ttf?raw=true'
                    )
    font_m = load_font(
                    font_url='https://github.com/andrew-paglinawan/QuicksandFamily/blob/master/fonts/statics/Quicksand-Medium.ttf?raw=true'
                    )
    return(font_b, font_r, font_m)

@st.cache_data(show_spinner=False, ttl=60*30)
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    return df


#Chart functions---------------------------
#calculate dynamic axis ticks based on max time per month
def get_axis_ticks(max_sec):
        n_ticks=4
        if round(max_sec/n_ticks/60/60)>0:
            steps = 60*60*(round(max_sec/n_ticks/60/60))
        elif round(max_sec/n_ticks/60)>0:
            steps = 60*(round(max_sec/6/60))
        else:
            steps = n_ticks
        return steps

#convert seconds into nice format on chart
def convert_time(sec):
        hour = sec // 3600
        sec %= 3600
        min = sec // 60
        sec %= 60
        return "%02d:%02d" % (hour, min) 

  
#process data for chart
def process_data(df):

    #find last month in dataset
    last_date = df["Activity Date"].max()
    start_month = last_date.replace(day=1)
    df_filtered = df[(df["Activity Date"] >= start_month) & (df["Activity Date"] <= last_date)]

    #get activity types
    top_three = df_filtered["Activity Type"].value_counts().index.to_list()

    activity_data = {}
    for act in top_three:
        sub = df_filtered[df_filtered["Activity Type"] == act]
        daily = sub.groupby(sub["Activity Date"].dt.date).agg({"Distance": "sum", "Moving Time": "sum"}).reset_index()
        activity_data[act] = daily

    return df_filtered, activity_data, last_date

#create visual
def create_visualisation(activity_data,last_date):

    #configs-------------------------------------
    act_color = ["#6DB4C8", "#FD7B5C", "#FBCA58", "#7E8384"]
    act_colormap = dict(zip(list(activity_data.keys()), act_color))
    colors = {"bg": "#FBF9F5", "text":"#2E3234"}

    n = len(activity_data)
    fig, axes = plt.subplots(n,1, figsize=(10,3*n), sharex=True)
    fig.set_facecolor(colors["bg"])
    if n == 1:
        axes = [axes]

    for ax,(act,df_line) in zip(axes, activity_data.items()):
        ax.plot(pd.to_datetime(df_line["Activity Date"]), df_line["Moving Time"]/3600,
                color=act_colormap.get(act,"#7E8384"), label=act)
        ax.set_ylabel("Hours", fontproperties=font_r, color=colors["text"])
        ax.legend(frameon=False, prop=font_m)
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)
        for pos in ["top", "right"]:
            ax.spines[pos].set_visible(False)

    axes[-1].set_xlabel("Date", fontproperties=font_r, color=colors["text"])

    month_label = last_date.strftime("%B %Y")
    plt.figtext(0.5,0.95,'My last month in sports'.upper(),
                ha="center",
                fontsize = 40,
                color=colors["text"],
                fontproperties=font_b)
    plt.figtext(0.5,0.91,month_label, ha="center",fontsize = 20, color=colors["text"], alpha=0.95, fontproperties=font_r)
    plt.figtext(0.5,0.05,'Data: Strava | Design: Lisa Hornung',ha="center", fontsize = 7, color=colors["text"], alpha=0.7,fontproperties=font_r)

    return fig

#Main app--------------------------------------------------------
st.title('My last month in sports')
st.markdown("#### Visualise your most recent activities")
st.write("")

#upload data
st.sidebar.subheader("Data upload")

with st.sidebar:
    st.write("")
    with st.expander("What data do I need?", expanded=False):
        st.markdown("""
        You’ll need to download your activity data from Strava. Follow [this guide](https://support.strava.com/hc/en-us/articles/216918437-Exporting-your-Data-and-Bulk-Export) 
        to get a data dump.
        """)
        st.markdown("""
        The folder should contain `activities.csv` which we will use.
        """)
    st.write("") 
    uploaded_file = st.file_uploader("Upload your Strava csv file", 
                                    accept_multiple_files=False,
                                    on_change=set_rerun_true())
    
    if uploaded_file is None:
        st.session_state["is_csv"] = None
        st.session_state["upload_success"] = None
        st.session_state["FormSubmitter:user_inputs-Create visualisation"] = None
    
    if (st.session_state["rerun_data_processing"]== True) & (uploaded_file is not None):
        try:
            df = load_data(uploaded_file)
            st.session_state["is_csv"] = True    
        except UnicodeDecodeError:
            st.warning("Whoops, incorrect file format. Make sure to upload a `.csv` file to use this app")
            st.session_state["is_csv"] = False
            st.session_state["upload_success"]=False   

    #run check if correct file
    data_flag = False

    if (st.session_state["is_csv"]==True) & (st.session_state["rerun_data_processing"]== True):
        columns = df.columns
        expected_columns = ['Activity ID', 'Activity Date', 'Activity Name', 
                                'Activity Type', 'Distance.1', 'Moving Time']
        missing_columns = []
        for column in expected_columns:
            if column not in columns:
                data_flag=True
                missing_columns.append(column)
        if data_flag==True:
            st.warning("""
                    Whoops, your dataset doesn't look quite right ...\n
                    It's missing the following columns: {}\n
                    Check that the dataset matches the expected format                 
                    """.format(str(missing_columns)))
        if data_flag==False:
            st.session_state["upload_success"] = True
            with st.spinner('Uploading data ...'):

                #reduce to relevant columns
                df = df[expected_columns].rename(columns={"Distance.1":"Distance"})

                #convert date column into datetime
                df["Activity Date"] = pd.to_datetime(df["Activity Date"])

                #load fonts---------------------------
                font_b, font_r, font_m = load_fonts()

                #display success message
                st.success("Data upload successful")

st.sidebar.divider() 
st.sidebar.subheader("About this app")
st.sidebar.write("Made by Lisa Hornung with `streamlit`, `matplotlib` and `pyfonts`.")
st.sidebar.markdown("""
            Visit my [website](https://inside-numbers.com/) 
            or get in touch on [Github](https://github.com/Lisa-Ho), 
            [Mastodon](https://fosstodon.org/@LisaHornung), 
            [Bluesky](https://bsky.app/profile/lisahornung.bsky.social).
            """)

#user inputs  
if st.session_state["upload_success"]==True:
    with st.form(key='user_inputs'):
        st.form_submit_button('Create visualisation', on_click=form_submit_callback())

st.markdown("\n")

#run visualisation
if st.session_state["FormSubmitter:user_inputs-Create visualisation"] is not None:
    df_filtered,activity_data,last_date = process_data(df)
    fig = create_visualisation(activity_data,last_date)
    st.write(fig)


#download image
if st.session_state["FormSubmitter:user_inputs-Create visualisation"] is not None:
    st.divider()
    st.write("")   
    plt.savefig("my-last-month-in-sports.png", bbox_inches="tight", pad_inches=0.8)
    with open("my-last-month-in-sports.png", "rb") as file:
        btn = st.download_button(
                    label="Download image",
                    data=file,
                    file_name="my-last-month-in-sports.png",
                    mime="image/png"
                )

    plt.savefig("my-last-month-in-sports.svg",bbox_inches="tight", pad_inches=0.8)
    with open("my-last-month-in-sports.svg", "rb") as file:
        btn = st.download_button(
                    label="Download svg",
                    data=file,
                    file_name="my-last-month-in-sports.svg",
                    mime="svg"
                )

if st.session_state["upload_success"] != True:
    st.image("https://github.com/Lisa-Ho/year-in-sports/blob/main/year_in_sports_example_output.png?raw=true",
             width=400)