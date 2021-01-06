import pickle
import pandas as pd
import numpy as np
from scipy_dev import scipy
from scipy.optimize import minimize
print(scipy.__version__)
import inverter_tools
import itertools

path_to_obs = '/home/robbie/Dropbox/inverter/vishnu_real_data'
path_to_pickles = '/home/robbie/Dropbox/KuKa_modelling/fitting/'
track_file_name = 'test_track.p'


signatures, start_dates, end_dates = inverter_tools.prep_obs(path_to_obs)

df = signatures['Ku_HH_RS2']

print(df.iloc[0])
print(df.iloc[-1])
print('===================')

for i in range(df.shape[0]):
    if np.isnan(df.iloc[i]).any():
        print(df.iloc[i])

start_date, end_date = '2019-11-29 09:00:00', '2019-12-02 09:00:00'
site_no = 2

def get_obs_dict(signatures,timestep):

    obs_dict = {}
    for freq, pol in itertools.product(['Ku','Ka'],['VV','HV','HH']):
        var = signatures[f'{freq}_{pol}_RS{site_no}'][str(start_date):str(end_date)]
        obs_dict[f'{freq}_{pol}_Mean'] = np.array(var.iloc[timestep])

    return(obs_dict)

obs_dict_0 = get_obs_dict(signatures, 0)

min_costs = []
min_params = []

for i in range(1, 10):
    data = pickle.load(open(f'{path_to_pickles}first_run_{i}.p', 'rb'))
    df = pd.DataFrame(data, columns=['params', 'cost', 'datetime'])

    # Get index of minimum cost
    min_cost = np.min(df['cost'])
    min_index = list(df['cost']).index(min_cost)
    best_params = df.iloc[min_index][0]

    min_costs.append(min_cost)
    min_params.append(best_params)

total_min_cost = np.min(min_costs)
total_min_index = min_costs.index(total_min_cost)
total_min_params = min_params[total_min_index]

print(total_min_cost)
print(inverter_tools.print_params(total_min_params))

initial_bounds = [(0.08,0.4), # Snow Depth
                 (0.6,1.5), # Ice Thickness
                 (0.1,3), # Ice Salinity
                 (790,920), # Ice Density
                 (255,270), # Temperature
                 (0.1,0.4), # Snow MCL
                 (0.1,1), # Ice MCL
                 (250,400), # Snow Density
#                  (0,1), # Snow Salinity
                 (0.3,1.5), # Snow RMS
                 (8,120), # Snow RCL
                 (0.1,2.3), # Ice RMS
                 (10,150)] # Ice RCL

bds = inverter_tools.print_params(initial_bounds)

mod = inverter_tools.print_params(total_min_params)

# Update iteratively

initial_guess_for_next_round = total_min_params.copy()

iterative_best_params = []
iterative_best_fun = []

for round in range(0, 25):
    # Get observations to match this round

    obs_dict = get_obs_dict(signatures, round)

    # Fit the model to the new observations

    print(f'Round {round} minimizing...')

    updated_fit = minimize(inverter_tools.calculate_cost,
                           initial_guess_for_next_round,
                           args=(obs_dict,),
                           bounds=initial_bounds,
                           method='L-BFGS-B')


    initial_guess_for_next_round = updated_fit.x

    iterative_best_params.append(initial_guess_for_next_round)
    iterative_best_fun.append(updated_fit.fun)
    print(updated_fit.fun)

res_dict = {
                'best_params' : iterative_best_params,
                'best_costs' : iterative_best_fun,
            }

pickle.dump(res_dict, open(f'{track_file_name}.p', 'wb'))