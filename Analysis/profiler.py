import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor
from Analysis.functions import position_num_map, frequency_transformation

rpt = Report_Extractor()
df = rpt.get_player_matches('Premiership', 2022)

cols_with_data = [col for col in df.columns if not df[col].isna().all()]
df = df[cols_with_data]

df= df[df['position_num'] > 0]
df = df[df['position_num'] < 16]

for col in df.columns:
    df[col] = pd.to_numeric(df[col]) 

features = df.columns[4:-2]

for feature in tqdm(features):
    df[feature] = df[[feature,'mins_played']].apply(frequency_transformation, axis=1)

df['position'] = list(map(position_num_map, df['position_num']))

df.to_csv('player_match_data.csv')



df_grp = df.groupby(['position']).agg(['mean', 'std', 'count'])

df_grp['tries']['mean'] + np.sqrt(df_grp['tries']['count'])*df_grp['tries']['std']



import plotly.express as px

fig = px.box(df, y='turnovers_won', x='position',
          hover_data=df.columns)
fig.show()
#wing stands out as try scorer

for f in features:
    fig = px.box(df, y=f, x='position',
          hover_data=df.columns)
    fig.show()

#this series of plots give some insights visually into which players perform
#which action most on the pitch and to the roles players are involved in

# offence
# wings score tries and tries are mostly assisted by halfs (centers do less so)
# halfs follow up with conversions and penalties (centers do less so)

#travel
# Full back , wing, number 8 and centre and half travel the most distance.
# All players carry but number 8 performs the most carries followed by full back

#Passing
# this is largely dominated by halfs. They do twice as much passing as any other player.
# notably prop,hooker, locks and flanks do not offload as much as other players

#Tackling
# All players tackle a fair bit but by a small amount the first two rows of scrum tackle more
# this being prop, hooker, locks, and flanks
# As for missing tackles props hooker and locks miss less tackles than other players

#Turnovers
# number 8, flankers and centers win more turnovers
# props concede the least number of turn overs with the scrum players and the centres 
# conceding less that half wings and full backs

#Lineouts
# Locks, flankers and number 8 win the most lineouts

# defenders beaten
# full backs, wings and centers beat more defenders where as number 8s beat alot also
# full backs, wings and centers get most of the clean breaks.

#### All of these observations paint a picture of how rugby players perform functions in a team

# Wings and Halfs work closely to score tries and conversions
# Halfs are the back bone to a teams passing game and given high number of try assists along with
# passing help facilitate wings to score tries
# wings and centres appear to be the players who can beat defenders by finding clean breaks
# number 8 and full backs beat defenders too but by seer power

# Full Backs and number 8s carry the ball up the pitch with wings likly carrying the ball
# the final distance to score tries

# All players need to tackle but it appears that the first two rows of scrum tackle the most
# and are usually more accurte meaning they function as the main stopping force for opposition

# Number 8, center and flankers function as great ball stealers win turnovers more for teams

# Simplified the rolls can be categorised as follows
# Point Scorers: Wings, Halfs, Centres
# Territory gain: Full back, number 8, Centre, Hooker and Flanker
# Tacklers: Prop, Lock, Hooker, Flanker and Number 8

