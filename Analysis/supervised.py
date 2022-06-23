import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor
from Analysis.elo_rating import add_elo_score
from Analysis.functions import position_num_map, frequency_transformation


#ML libs
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


def show_feature_imps(features, target, df, position):
    #clf for wings
    df_pos = df[df['position']==position]

    X, y = df_pos[features], df_pos[target]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=69)

    #Pipeline
    pipe = Pipeline([('scaler', StandardScaler()),
                     ('rf', RandomForestRegressor(random_state=69))])

    param_grid = {
        "rf__n_estimators": [100, 500],
        "rf__max_depth": [4, 8, 12],
        "rf__max_features": ['auto','sqrt'],
        'rf__max_leaf_nodes': [16,32]
        }

    cv = GridSearchCV( pipe, param_grid, n_jobs=-1, cv=10, verbose=10)
    cv.fit(X_train, y_train.values.ravel())

    print('The best score was: ', cv.best_score_, ' with the following parameters.\n')
    print(cv.best_params_)

    cv.best_params_


    F_imp = [[f, imp] for f, imp in zip(list(features), list(cv.best_estimator_[-1].feature_importances_))]
    df_F_imp = pd.DataFrame(F_imp, columns = ['feature', 'importance'])

    #plot of most important features
    import seaborn as sns
    import matplotlib.pyplot as plt
    ax = sns.barplot(x="importance", y="feature", data=df_F_imp)
    plt.title('Feature Importances for {0}, Accuracy={1}'.format(position, np.round(cv.best_score_,4)))
    plt.show()

    return 0



rpt = Report_Extractor()

comp = 'Premiership'
year = 2022

df_m = rpt.get_matches(comp, year)
df_pm = rpt.get_player_matches(comp, year)

#df = add_elo_score(df_m, df_pm)

#find columns not all na
cols_with_data = [col for col in df.columns if not df[col].isna().all()]
df = df[cols_with_data]
#remove position numbers that are not gathered correctly
df= df[df['position_num'] > 0]
df = df[df['position_num'] < 16]

#only keep examples where 20+ mins played
df = df[df['mins_played']>20]

#make numeric
#for col in df.columns:
#    df[col] = pd.to_numeric(df[col]) 

#map position numbers
df['position'] = list(map(position_num_map, df['position_num']))


features = ['meters_made', 'carries',
       'passes_made', 'offloads', 'tackles_made', 'missed_tackles',
       'turnovers_won', 'turnovers_conceded', 'lineouts_won',
       'lineouts_stolen', 'defemders_beaten', 'clean_breaks']

for feature in tqdm(features):
    df[feature] = df[[feature,'mins_played']].apply(frequency_transformation, axis=1)

target = 'elo_rating'




show_feature_imps(features, target, df, 'Prop')

show_feature_imps(features, target, df, 'Second Row')

show_feature_imps(features, target, df, 'Number 8')

show_feature_imps(features, target, df, 'Scrum Half')

show_feature_imps(features, target, df, 'Fly Half')

show_feature_imps(features, target, df, 'Wing')

show_feature_imps(features, target, df, 'Centre')

show_feature_imps(features, target, df, 'Full Back')