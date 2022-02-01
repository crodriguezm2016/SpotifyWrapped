import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import ipywidgets as ipw
import numpy as np
from urllib.request import urlopen
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth


# Functions
def toMinutes(x):
  newTime = x / 60000
  return newTime

def toHours(x):
  newTime = toMinutes(x) / 60
  return newTime

def toDay(x):
  newTime = toHours(x) / 24
  return(newTime)

monthsSelection = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def GetPlaylistID(username, playlist_name):
    playlist_id = ''
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
    return playlist_id

def GetSongID(df, trackColName, artistColName):
    songIdList = []
    for rows in range(len(df)):
        result = sp.search(q=f"{df[trackColName][rows]} {df[artistColName][rows]}", limit=1, type='track')
        songid = result['tracks']['items'][0]['id']
        songIdList.append(songid)
    return songIdList

#Sidebar

with st.sidebar.header('1. Upload your Spotify JSON data:'):
    uploaded_file1 = st.sidebar.file_uploader("Upload your Streaming History JSON file", key="lauren")
    uploaded_file2 = st.sidebar.file_uploader("Upload your Streaming History JSON file", key='solari')
    uploaded_file3 = st.sidebar.file_uploader("Upload your Streaming History JSON file", key='pom')
    uploaded_file4 = st.sidebar.file_uploader("Upload your Streaming History JSON file", key='udon')

if (uploaded_file1 is None) and (uploaded_file2 is None) and (uploaded_file3 is None) and (uploaded_file4 is None):
    #st.sidebar.markdown("Currently using the WebApp Owner's data...")
    with urlopen('https://raw.githubusercontent.com/crodriguezm2016/SpotifyWrapped/main/DemoSpotifyData/StreamingHistory0.json') as response:
        df1 = pd.json_normalize( json.load(response) )
    with urlopen('https://raw.githubusercontent.com/crodriguezm2016/SpotifyWrapped/main/DemoSpotifyData/StreamingHistory1.json') as response:
        df2 = pd.json_normalize( json.load(response) )
    with urlopen('https://raw.githubusercontent.com/crodriguezm2016/SpotifyWrapped/main/DemoSpotifyData/StreamingHistory2.json') as response:
        df3 = pd.json_normalize( json.load(response) )
    df = df1.append(df2)
    df = df.append(df3)
    st.sidebar.markdown('Data from the webapp owner is used.')

else:
    df = pd.DataFrame()
    if (uploaded_file1 is not None):
        df = df.append(pd.read_json(uploaded_file1))
    if (uploaded_file2 is not None):
        df = df.append(pd.read_json(uploaded_file2))
    if (uploaded_file3 is not None):
        df = df.append(pd.read_json(uploaded_file3))
    if (uploaded_file4 is not None):
        df = df.append(pd.read_json(uploaded_file4))

with st.sidebar.header('2. Choose how granular you want to see your data:'):
    numArtists = st.sidebar.slider("Number of Top Artists", min_value=1, max_value=10, value=5, key='Feyde')

    numTracks = st.sidebar.slider("Number of Top Tracks", min_value=1, max_value=10, value=5, key='publicLibraryCommute')

with st.sidebar.header('3. Choose which months of data should be displayed: '):
    selectedMonths = st.sidebar.multiselect("Month Range", options = monthsSelection, default=monthsSelection)

with st.sidebar.header('4. Choose the way time is displayed: '):
    timeChoice = st.sidebar.radio("Time: ", options=("Minutes", "Hours"))
    if timeChoice == "Minutes":
        timeAlter = toMinutes
    else:
        timeAlter = toHours

unitTime = timeAlter.__name__.replace('to','').lower()
colname = "timePlayed" + unitTime

#Turn endtime into a datetime object
df.endTime = pd.to_datetime(df.endTime)

selectedMonthsNum = [monthsSelection.index(x) + 1 for x in selectedMonths]

filteredData = df[df.endTime.dt.month.isin(selectedMonthsNum)]
#filteredData = df

#Metric Numbers
dataStart = min(filteredData.endTime).date()
dataStop = max(filteredData.endTime).date()

dataTimeDiff = str( (dataStop - dataStart).days )

totalTimePlayed = round(timeAlter(sum(filteredData.msPlayed)),0)
totalListens = len(filteredData.trackName)

uniqueArtists = len(filteredData.artistName.unique())
uniqueTracks = len(filteredData.trackName.unique())

with st.sidebar.header('5. Choose how to pick top artist/tracks: '):
    timeSort = st.sidebar.radio("Sorting Method", options=("Time Listened", "Number of Plays"))
    if timeSort == "Time Listened":
        timeSort = colname
        sortTitle = 'Time'
        percentOfTotalCalc = totalTimePlayed
    else:
        timeSort = 'numTracksListened'
        sortTitle = 'Plays'
        percentOfTotalCalc = totalListens


#Artist Data
artistTime = filteredData[["artistName", "msPlayed", 'trackName']]
artistTime = artistTime.groupby(['artistName'], as_index=False).agg({'msPlayed' : 'sum', 'trackName' : 'count'})

artistTime[colname] = round(timeAlter(artistTime.msPlayed),0).apply(lambda x: int(x))

artistTime = artistTime.drop(["msPlayed"], axis = 1)

artistTime = artistTime.rename(columns={'trackName' : 'numTracksListened'})
artistTime = artistTime.sort_values(by = [timeSort, 'artistName'], ignore_index=True, ascending=False)

topArtists = artistTime.head(numArtists)

topArtists['percentOfTotal'] = topArtists[timeSort].apply(lambda x : str( round(x / percentOfTotalCalc * 100, 2) ) + '%')

topArtists['firstListened'] = topArtists.artistName.apply(lambda x : str(min(df.endTime[df.artistName == x])).split()[0]  )
topArtists['lastListened'] = topArtists.artistName.apply(lambda x : str(max(df.endTime[df.artistName == x])).split()[0]  )


#Artist Fig
topArtistsFig =  go.Figure( data=[go.Bar( x = topArtists.artistName, y = topArtists[timeSort], textposition= 'auto',
                                         text = topArtists[colname].apply(lambda x : str(x) + ' ' + unitTime),
                                         customdata=topArtists[['percentOfTotal', 'firstListened', 'lastListened', 'numTracksListened']],
                                         hovertemplate =
                                         '<b>%{x}</b><br>'  
                                         '%{customdata[0]} of Total Listening<br>' +
                                         'First Listen: %{customdata[1]}<br>' +
                                         'Latest Listen: %{customdata[2]}<br>' +
                                         'Number of Tracks Listened to: %{customdata[3]}<br>',
                                         name = ''
                                         )])
topArtistsFig.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                            marker_line_width=1.5, opacity=0.8)
topArtistsFig.update_layout(title = dict(text = 'Your Top {} Artists by {}'.format(numArtists, sortTitle), font_size = 24), 
                            plot_bgcolor = 'rgb(255,255,255)')


#Track Data
trackTime = df[["trackName", "msPlayed", 'artistName', 'endTime']]
trackTime = trackTime.groupby(['trackName', 'artistName'], as_index=False).agg({'msPlayed' : 'sum', 'endTime' : 'count'})

trackTime[colname] = round(timeAlter(trackTime.msPlayed),0).apply(lambda x: int(x))
trackTime = trackTime.drop(["msPlayed"], axis = 1)

trackTime = trackTime.rename(columns={'endTime' : 'numTracksListened'})
trackTime = trackTime.sort_values(by = [timeSort, 'trackName'], ignore_index=True, ascending=False)

topTracks = trackTime.head(numTracks)

topTracks['percentOfTotal'] = topTracks[timeSort].apply(lambda x : str( round(x / percentOfTotalCalc * 100, 2) ) + '%')

topTracks['firstListened'] = topTracks.trackName.apply(lambda x : str(min(df.endTime[df.trackName == x])).split()[0]  )
topTracks['lastListened'] = topTracks.trackName.apply(lambda x : str(max(df.endTime[df.trackName == x])).split()[0]  )


#Track Fig
topTracksFig =  go.Figure( data=[go.Bar( x = topTracks.trackName, y = topTracks[colname], textposition= 'auto',
                                         text = topTracks[colname].apply(lambda x : str(x) + ' ' + unitTime),
                                         customdata=topTracks[['percentOfTotal', 'firstListened', 'lastListened', 'numTracksListened', 'artistName']],
                                         hovertemplate =
                                         '<b>%{x} by %{customdata[4]}</b><br>'  
                                         '%{customdata[0]} of Total Listening<br>' +
                                         'First Listen: %{customdata[1]}<br>' +
                                         'Latest Listen: %{customdata[2]}<br>' +
                                        'Number of Listens: %{customdata[3]}<br>',
                                         name = ''
                                         )])
topTracksFig.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                            marker_line_width=1.5, opacity=0.8)
topTracksFig.update_layout(title = dict(text = 'Your Top {} Tracks'.format(numTracks), font_size = 24), 
                            plot_bgcolor = 'rgb(255,255,255)')


#Create Main Webpage

st.title("Spotify \"Wrapped\"")

st.markdown("""
**Welcome** to my take on :notes: Spotify \"Wrapped\" :notes:! As a data nerd :chart_with_upwards_trend:, I was always curious about some of the nitty gritty details of Spotify Wrapped and I wished I had more data and details on my listening. 
This webapp aims to do exactly that! Use the steps below to download your data and use this webapp, or, use my own data as a sample dataset.

1. Sign into your Spotify Account at this [link](https://www.spotify.com/us/account/overview/).
2. You should now be in your Privacy Settings, if not, click on Privacy Settings on the left.
3. At the bottom of the page, request your data.
4. Check your email for a confirmation to download your data and wait for a zip file from Spotify (this usually takes a day or two).
5. Once you get your zip file, unzip it and locate the files that are labeled 'StreamingHistory', there will probably be a few of these.
6. Upload these files to the app with the buttons on the sidebar!
7. Customize your experience and enjoy!

I would welcome any feedback or ideas:bulb: that you have for this project. Please use [this Google form](https://docs.google.com/forms/d/e/1FAIpQLSeg5gwJbCYb68I0nGls3DHuFcVdJcPRyImesRfgg-PnBN8xUA/viewform?usp=sf_link) to submit feedback.
To learn more about me or other projects that I am working on, check out [my website](https://carlosrodriguezm.com/) or my [LinkedIn](https://www.linkedin.com/in/crodriguezmunoz/).
""")

st.subheader("Overview Stats:")
col1, col2, col3 = st.columns(3)
col1.metric("Number of Unique Artists", uniqueArtists)
col2.metric("Number of Unique Songs", uniqueTracks)
col3.metric("Listening in {}".format(unitTime), totalTimePlayed)


col4,col5, col6 = st.columns(3)
col4.metric("Data Start", str(dataStart) )
col5.metric("Data End", str(dataStop) )
col6.metric("Data Length in Days", str(dataTimeDiff))

st.subheader("Breakdown by Artists:")
st.plotly_chart(topArtistsFig)
st.table(topArtists)

st.subheader("Breakdown by Tracks:")
st.plotly_chart(topTracksFig)
st.table(topTracks)

#New Additions
st.subheader("Create a Playlist with Your Top Songs!")
st.markdown("""
Based on your specificions in your side bar, the webapp has found your top tracks and can create a playlist for you! 
If you click the button below, you will be prompted to enter a playlist name and will be redirected to authorize access for the webapp to create the playlist for you.
""")
if st.button('Create Your Playlist!'):
    numTracksPlaylist = st.slider('Select how many top tracks you want included:', min_value=5, max_value=10)
    trackSearch = trackTime.head(numTracksPlaylist)[['trackName', 'artistName']]
    playlist_name = st.text_input('Playlist Name')
    scope = "playlist-modify-public"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope,client_id= '8b57b4aa204b4d689c0e1fc896573ae9', client_secret='674262ccbc884a42a4cb4db49516f4a0', redirect_uri='https://spotifywrapped.carlosrodriguezm.com/'))
    username = sp.me()['id']
    sp.user_playlist_create(user = username, name=playlist_name)
    playlist_id = GetPlaylistID(username, playlist_name)
    songIdList = GetSongID(trackSearch, 'trackName', 'artistName')
    sp.user_playlist_add_tracks(username, playlist_id, songIdList)
    st.write('Playlist Created!')
else:
    st.write('What are you waiting for!')