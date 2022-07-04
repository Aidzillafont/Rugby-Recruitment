import math

def position_num_map(x):
    pos_map = { 1: 'Prop',
               2: 'Prop', #hooker
               3: 'Prop',
               4: 'Second Row', #lock
               5: 'Second Row', #lock
               6: 'Second Row', #flanker
               7: 'Second Row', #flanker
               8: 'Number 8',
               9: 'Scrum Half',
               10: 'Fly Half',
               11: 'Wing',
               12: 'Centre',
               13: 'Centre',
               14: 'Wing',
               15: 'Full Back'
               }
    return pos_map[x]

def frequency_transformation(x):
    if x.isnull().values.any():
        return None

    #last minute subs
    x[1] = 10 if x[1] <= 10 else x[1]

    q = 80/float(x[1])
    return( (float(x[0])*q)/(math.log10(q)+1))
