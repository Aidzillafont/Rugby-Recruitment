import os
import pickle
import numpy as np
import pandas as pd

pickle_path = os.getcwd() + '\\Scrapers\\Scraped Data\\premiership_dict.pkl'
with open(pickle_path, 'rb') as f:
    loaded_dict = pickle.load(f)

#ID
pid = np.array([i for i in loaded_dict])

#features
clean_breaks =  np.array([float(loaded_dict[i]['stat_dict'].get('Clean Breaks', '0')) for i in loaded_dict])
defenders_beaten =  np.array([float(loaded_dict[i]['stat_dict'].get('Defenders Beaten', '0')) for i in loaded_dict])
offloads =  np.array([float(loaded_dict[i]['stat_dict'].get('Offloads', '0')) for i in loaded_dict])
carries =  np.array([float(loaded_dict[i]['stat_dict'].get('Carries', '0')) for i in loaded_dict])
meters = np.array([float(loaded_dict[i]['stat_dict'].get('Meters', '0')) for i in loaded_dict])
avg_mpc = np.array([float(loaded_dict[i]['stat_dict'].get('Average Metres Per Carry', '0m').strip('m')) for i in loaded_dict])
height = np.array([float(loaded_dict[i]['profile_dict'].get('Height:', '0m').split('m', 1)[0]) for i in loaded_dict])
weight = np.array([float(loaded_dict[i]['profile_dict'].get('Weight:', '0kg').split('k', 1)[0]) for i in loaded_dict])
position = np.array([loaded_dict[i]['profile_dict'].get('Position:') for i in loaded_dict])

#target
tries = np.array([float(loaded_dict[i]['stat_dict'].get('Tries','0')) for i in loaded_dict])

df = pd.DataFrame({'tries': tries, 'clean_breaks': clean_breaks, 'defenders_beaten': defenders_beaten, 'offloads': offloads, 'carries': carries, 'meters': meters, 'avg_mpc': avg_mpc, 'height': height, 'weight': weight, 'position': position, })

#df = pd.DataFrame(columns = ['tries', 'position', 'weight', 'height', 'avg_mpc', 'meters', 'carries', 'offloads', 'defenders_beaten', 'clean_breaks'],
#                  data = [tries, position, weight, height, avg_mpc, meters, carries, offloads, defenders_beaten, clean_breaks])

print(df)

features = ['clean_breaks', 'defenders_beaten', 'offloads', 'carries', 'meters', 'avg_mpc', 'height', 'weight', 'position'] 
label = ['tries']

#our label is imbalanced here so need to manage this
print('our label is imbalanced here so need to manage this: ', df["tries"].value_counts(), sep='\n')

#models
from sklearn.ensemble import RandomForestClassifier

#preprocess steps
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer

#train test splitter and grid search
from sklearn.model_selection import train_test_split, GridSearchCV

#pipline 
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

X = df[features]
y = df[label].astype(str) #since we are going to use a classifier

#numeric 
numeric_feat = ['clean_breaks', 'defenders_beaten', 'offloads', 'carries', 'meters', 'avg_mpc', 'height', 'weight']
numeric_trans = Pipeline([ 
                          ('imputer', SimpleImputer()), 
                          ('scaler', StandardScaler()), 
])

#catagories
cata_feat = ['position']
#since our test will likely contain classes not in training 
#we need to tell our ordinal encoder use -1 for unknown values 
cata_trans = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1) 

preprocessor = ColumnTransformer([
                                  ('num', numeric_trans, numeric_feat),
                                  ('cat', cata_trans, cata_feat),
])

#pipleine it all together with a model
model = Pipeline([
                  ('preprocess', preprocessor),
                  ('rf', RandomForestClassifier(class_weight='balanced')) #this is our imbalance handler
])

#split our test train
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)

#fit and score the model
model.fit(X_train, y_train.values.ravel() )
print("model score: %.3f" % model.score(X_test, y_test.values.ravel() ))

print('Guessing the most common class would give you: ', 219/518, sep='')


from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

conf_mat = confusion_matrix(y_test, model.predict(X_test), labels=model.classes_)
print(conf_mat)

import matplotlib.pyplot as plt

disp = ConfusionMatrixDisplay(confusion_matrix=conf_mat,
                              display_labels=model.classes_)
disp.plot()
plt.show()