###### PCA - SIX NATIONS ######
from pandas import read_csv
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import numpy as np

filepath = os.getcwd() + '\\Profile Constructor\\Profile_Data\\sixnations_profile_dist.csv'

features = ['T','TA','C','P','DG','M','CA','MK','PM','O','BTs','Kon','TM','MT','TW','TC','HE','PC','OPC','SPC','LW','LS','YC','RC']
features = ['{0}_per80m|mean'.format(col) for col in features]

label = ['pos_num_y']

df = read_csv(filepath)
arr = df[features].values
n_pcs = 3
pca = PCA(n_components=n_pcs)

scaler = StandardScaler()
X = scaler.fit_transform(arr)

fit = pca.fit(X)
print("Explained Variance: {0}".format(fit.explained_variance_ratio_))
print(fit.components_)


most_important = [np.abs(pca.components_[i]).argmax() for i in range(n_pcs)]
most_important
[features[imp] for imp in most_important]


for i in range(n_pcs):
    pc_1 = abs(pca.components_[i])
    most_important = np.argpartition(pc_1, - n_pcs)[-n_pcs:]
    loadings = [(features[imp], round(pc_1[imp],2)) for imp in most_important]
    print('PC-{0}: explains {1}% of variance and its most Important Components are (Name, Loading): '.format(i, round(pca.explained_variance_ratio_[i]*100) ), 
          list(reversed(loadings)),'------------------------------', sep='\n' )

### Remove features with low variance ###
from sklearn.feature_selection import VarianceThreshold

sel = VarianceThreshold(threshold=(.8 * (1 - .8)))

sel.fit_transform(X)

variances = sel.variances_

boolArr = variances < (.8 * (1 - .8))
removed = np.where(boolArr)[0][0]
features[removed]

### additional unsupervised
### high correlation data 
### clustering


### others are supervised

### Univariate feature selection ###
from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import chi2
