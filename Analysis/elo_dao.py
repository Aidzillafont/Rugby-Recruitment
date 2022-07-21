import pandas as pd
import os
import math
from tqdm import tqdm
import numpy as np
import sys
##needed for debugging
sys.path.append('.')
from Database.db_api import Report_Extractor

from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer 
from sklearn.inspection import permutation_importance

import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.feature_selection import SelectKBest

#preprocess steps
from sklearn.preprocessing import StandardScaler, OneHotEncoder

#pipline 
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import GridSearchCV

from sklearn.model_selection import train_test_split, GridSearchCV
# performace analysers
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.ensemble import RandomForestClassifier


def plot_permutation_importance(best_estimator, X, y, features, label, best_score):
    x_processed = best_estimator[0].transform(X)
    feat_imp = permutation_importance(best_estimator[1], x_processed, y, random_state=101, n_repeats=50, n_jobs=-1).importances_mean
    F_imp = [[f, imp] for f, imp in zip(list(features), list(feat_imp))]
    df_F_imp = pd.DataFrame(F_imp, columns = ['feature', 'decrease in accuracy'])
    ax = sns.barplot(x="decrease in accuracy", y="feature", data=df_F_imp)
    plt.title('Feature Importances: Target={0}, Accuracy={1}'.format(label, np.round(best_score,4)))
    plt.savefig('books_read.png', bbox_inches='tight')
    top_features = df_F_imp.sort_values(by=['decrease in accuracy'], ascending=False)[:5]['feature'].to_list()
    return(top_features)

def run_model_and_evaluate(model, df, numeric_feat,  cata_feat, label, param_grid, built_in_F_IMP=True):

    features = numeric_feat + cata_feat
    X = df[features]
    y = df[label]

    #split our test train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=101)
    #pipleine it all together with a model

   
    numeric_trans = Pipeline([ 
                              ('imputy', SimpleImputer(strategy='mean')), 
                              #('select',SelectKBest(k=10)),
                              ('scaler', StandardScaler()), 
    ])

    cata_trans = OneHotEncoder() 

    #bundle our preprocessers together
    preprocessor = ColumnTransformer([
                                      ('num', numeric_trans, numeric_feat),
                                      ('cat', cata_trans, cata_feat),
    ])

    pipe = Pipeline([
                    ('preprocess', preprocessor),
                    ('clf', model) #this is our imbalance handler
    ])

    #fit and score the model
    cv = GridSearchCV( pipe, param_grid, n_jobs=-1, cv=5, verbose=10)
    cv.fit(X_train, y_train.values.ravel())

    rf_best_score_train = cv.best_score_
    rf_best_score_test = cv.best_estimator_.score(X_test, y_test)
    rf_cm = confusion_matrix(y_test, cv.predict(X_test))
    rf_score_detail = classification_report(y_test, cv.predict(X_test))

    print('The best score on training was: ', rf_best_score_train, 
        'The best score on test was: ', rf_best_score_test, 
        'With the following confusion matrix', rf_cm,
        'And the following precision and recall', rf_score_detail,
        'with the following parameters.', cv.best_params_ , sep='\n')

    if built_in_F_IMP:
        F_imp = [[f, imp] for f, imp in zip(list(features), list(cv.best_estimator_[-1].feature_importances_))]
        df_F_imp = pd.DataFrame(F_imp, columns = ['feature', 'importance'])

        #plot of most important features
    
        ax = sns.barplot(x="importance", y="feature", data=df_F_imp)
        plt.title('Feature Importances: Target={0}, Accuracy={1}'.format(label, np.round(cv.best_score_,4)))
        plt.savefig('books_read.png', bbox_inches='tight')
        top_features = df_F_imp.sort_values(by=['importance'], ascending=False)[:5]['feature'].to_list()

    else:
        top_features = plot_permutation_importance(cv.best_estimator_, X_train, y_train, features, label, cv.best_score_)
  
    return ([cv, rf_best_score_train, rf_best_score_test, rf_cm, rf_score_detail, top_features])


rpt = Report_Extractor()

df = pd.DataFrame(rpt.find('Players',['*'], true=True))

df = df.loc[df['games_played']>=10]

#df.loc[df['most_common_position_num'].isin([1,2])]

#train test splitter and grid search

cata_feat = ['most_common_position_num']

numeric_feat = ['games_played', 'm_tries', 's_tries', 'm_try_assist', 's_try_assist',
       'm_conversions', 's_conversions', 'm_penalty_goals', 's_penalty_goals',
       'm_meters_made', 's_meters_made', 'm_carries', 's_carries',
       'm_passes_made', 's_passes_made', 'm_offloads', 's_offloads',
       'm_tackles_made', 's_tackles_made', 'm_missed_tackles',
       's_missed_tackles', 'm_turnovers_won', 's_turnovers_won',
       'm_turnovers_conceded', 's_turnovers_conceded', 'm_lineouts_won',
       's_lineouts_won', 'm_defenders_beaten', 's_defenders_beaten', 'm_clean_breaks',
       's_clean_breaks', ]



##more EDA to be done #pehaps on notebook
#import matplotlib.pyplot as plt
#import seaborn as sns
#sns.set_theme(style="ticks")

#sns.pairplot(df[['most_common_position_num', 'games_played', 'attack_score', 'm_tries', 'm_try_assist',
#       'm_conversions', 'm_penalty_goals', ]], hue='most_common_position_num')
#plt.show()


#sns.pairplot(df[['most_common_position_num', 'games_played','open_score', 'm_passes_made', 'm_offloads',
#       'm_carries', 'm_penalty_goals', ]],  hue='most_common_position_num')
#plt.show()


#sns.pairplot(df[['most_common_position_num', 'games_played','defense_score', 'm_tackles_made', 'm_missed_tackles',
#       'm_turnovers_won', 'm_turnovers_conceded', ]],  hue='most_common_position_num')
#plt.show()




#sns.displot(df, x="elo_score", hue="most_common_position_num", stat="density")
#plt.show()


#sns.displot(df, x="attack_score", hue="most_common_position_num", stat="density")
#plt.show()

#sns.displot(df, x="open_score", hue="most_common_position_num", stat="density")
#plt.show()

#sns.displot(df, x="defense_score", hue="most_common_position_num", stat="density")
#plt.show()

df[['elo_score','attack_score','open_score', 'defense_score']]=df[['elo_score','attack_score','open_score', 'defense_score']].apply(pd.to_numeric)
df[['elo_score','attack_score','open_score', 'defense_score']].describe()

#we will categorise players based on 3 way split of values bottom 3rd poor  top 3rd good
# - 1 is poor, 0 is average, +1 is good
df['elo_label'] = pd.qcut(df['elo_score'], 3 , labels=[-1,0,1])
df['attack_label'] = pd.qcut(df['attack_score'], 3 , labels=[-1,0,1])
df['open_label'] = pd.qcut(df['open_score'], 3 , labels=[-1,0,1])
df['defense_label'] = pd.qcut(df['defense_score'], 3 , labels=[-1,0,1])



#Lets run some models




rf_results_elo = run_model_and_evaluate(RandomForestClassifier(class_weight='balanced', random_state=101),
                                    df, numeric_feat, cata_feat, 'elo_label',
                                    param_grid = {
                                        "clf__n_estimators": [100, 300],
                                        "clf__criterion": ['entropy'],
                                        "clf__max_depth": [8, 16],
                                        'clf__max_leaf_nodes': [8, 16]
                                        }
                                    )



#rf_results_elo[0].best_estimator_.named_steps['preprocess'].transformers[0][1].named_steps['select'].get_support(indices=True)


rf_results_attack = run_model_and_evaluate(RandomForestClassifier(class_weight='balanced', random_state=101),
                                    df,  numeric_feat, cata_feat, 'attack_label',
                                    param_grid = {
                                        "clf__n_estimators": [100, 300],
                                        "clf__criterion": ['entropy'],
                                        "clf__max_depth": [8, 16],
                                        'clf__max_leaf_nodes': [8, 16]
                                        }
                                    )


rf_results_open = run_model_and_evaluate(RandomForestClassifier(class_weight='balanced', random_state=101),
                                    df, numeric_feat, cata_feat, 'open_label',
                                    param_grid = {
                                        "clf__n_estimators": [100, 300],
                                        "clf__criterion": ['entropy'],
                                        "clf__max_depth": [8, 16],
                                        'clf__max_leaf_nodes': [8, 16]
                                        }
                                    )


rf_results_defense = run_model_and_evaluate(RandomForestClassifier(class_weight='balanced', random_state=101),
                                    df, numeric_feat, cata_feat, 'defense_label',
                                    param_grid = {
                                        "clf__n_estimators": [100, 300],
                                        "clf__criterion": ['entropy'],
                                        "clf__max_depth": [8, 16],
                                        'clf__max_leaf_nodes': [8, 16]
                                        }
                                    )



df['overall_score'] = df[['elo_label','attack_label','open_label', 'defense_label']].sum(axis=1)
df['overall_label'] = pd.qcut(df['overall_score'],3,[-1,0,1])

rf_results_overall = run_model_and_evaluate(RandomForestClassifier(class_weight='balanced', random_state=101),
                                    df, numeric_feat, cata_feat, 'overall_label',
                                    param_grid = {
                                        "clf__n_estimators": [100, 300],
                                        "clf__criterion": ['entropy'],
                                        "clf__max_depth": [8, 16],
                                        'clf__max_leaf_nodes': [8, 16]
                                        }
                                    )


df['overall_label'].value_counts()



df.iloc[:,3:] = df.iloc[:,3:].apply(pd.to_numeric)
corr = df.corr()
plt.figure(figsize=(12,6))
sns.heatmap(corr.loc[numeric_feat ,['elo_label','attack_label','open_label','defense_label','overall_label']], annot=True, yticklabels=1 )
plt.show()




corr = df.corr()
plt.figure(figsize=(12,6))
sns.heatmap(corr.loc[: , ['m_defenders_beaten'] ], annot=True, yticklabels=1 )
plt.show()

df.info()

from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC

rf_results_elo = run_model_and_evaluate(GaussianNB(),
                                    df, numeric_feat, cata_feat, 'elo_label',
                                    param_grid = {
                                        "clf__var_smoothing": [1e-8,1e-9, 1e-10],
                                        },
                                    built_in_F_IMP=False
                                    )


rf_results_elo = run_model_and_evaluate(XGBClassifier(),
                                    df, numeric_feat, cata_feat, 'elo_label',
                                    param_grid = {
                                        'clf__n_estimators':[100,300],
                                        'clf__max_depth':[8, 16],
                                        'clf__eta':[0.025,0.05,0.1] 
                                        }
                                    )

rf_results_elo = run_model_and_evaluate(DecisionTreeClassifier(),
                                    df, numeric_feat, cata_feat, 'elo_label',
                                    param_grid = {
                                        'clf__criterion':['gini','entropy'],
                                        'clf__max_depth':[16,32,64],
                                        }
                                    )

rf_results_elo = run_model_and_evaluate(SVC(),
                                    df, numeric_feat, cata_feat, 'elo_label',
                                    param_grid = {
                                        'clf__kernel':['linear', 'poly', 'rbf', 'sigmoid', 'precomputed'],
                                        },
                                    built_in_F_IMP=False
                                    )

