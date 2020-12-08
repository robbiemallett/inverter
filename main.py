import datetime
from inverter_classes import MyBounds, MyTakeStep
from inverter_tools import calculate_cost, prep_obs, CL_parse
try:
    from scipy_dev import scipy
except:
    pass

from scipy.optimize import basinhopping
import scipy
import numpy as np
import pickle
import sys

CL_input = CL_parse(sys.argv)
job_name = 'exp'+str(CL_input['task_id'])
niter = CL_input['niter']
hpc = CL_input['hpc']

print(f'scipy v{scipy.__version__}')
print(f'job_name: {job_name}')
print(f'hops: {niter}')
print(f"hpc: {hpc}")

initial_guess = [0.25, # Snow Depth
                 0.7, # Ice Thickness
                 0.5, # Ice Salinity
                 830, # Ice Density
                 260, # Temperature
                 0.3, # Snow MCL
                 0.34, # Ice MCL
                 350, # Snow Density
#                  0, # Snow Salinity
                 0.5, # Snow RMS
                 20, # Snow RCL
                 2.1, # Ice RMS
                 120] # Ice RCL

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

start_date, end_date = '2019-11-29 09:00:00', '2019-12-02 09:00:00'
site_no = 2

if hpc:
    path_to_obs = '/home/ucfarm0/inverse_smrt/inverter/vishnu_real_data'
    output_location = ''
else:
    path_to_obs = 'vishnu_real_data'
    output_location = 'output/'

signatures, start_dates, end_dates = prep_obs(path_to_obs)

Ku_VV = signatures[f'Ku_VV_RS{site_no}'][str(start_date):str(end_date)]
Ka_VV = signatures[f'Ka_VV_RS{site_no}'][str(start_date):str(end_date)]
Ku_HV = signatures[f'Ku_HV_RS{site_no}'][str(start_date):str(end_date)]
Ka_HV = signatures[f'Ka_HV_RS{site_no}'][str(start_date):str(end_date)]
Ku_HH = signatures[f'Ku_HH_RS{site_no}'][str(start_date):str(end_date)]
Ka_HH = signatures[f'Ka_HH_RS{site_no}'][str(start_date):str(end_date)]

obs_dict = {'Ku_VV_Mean': np.array(Ku_VV.iloc[0]),
            'Ka_VV_Mean': np.array(Ka_VV.iloc[0]),
            'Ku_HV_Mean': np.array(Ku_HV.iloc[0]),
            'Ka_HV_Mean': np.array(Ka_HV.iloc[0]),
            'Ku_HH_Mean': np.array(Ku_HH.iloc[0]),
            'Ka_HH_Mean': np.array(Ka_HH.iloc[0]),
            }

running_data = []

def store_minima(x, f, accepted):
    running_data.append((x, f, datetime.datetime.now()))
    pickle.dump(running_data, open(f'{output_location}{job_name}.p', 'wb') )

t_start = datetime.datetime.now()

print('running bh')
fit2 = basinhopping(calculate_cost,
                    x0 = initial_guess,
                    stepsize=1,
                    niter=niter,
                    minimizer_kwargs={
                        'method':'SLSQP',
                        'args':(obs_dict,), # Passes through the observations for the cost function calculation
                        'bounds':initial_bounds, # Stops the local minimizer exceeding bounds
                                        },
                    take_step=MyTakeStep(initial_bounds), # Ensures that parameter-space is evenly stepped through
                    accept_test=MyBounds(initial_bounds), # Stops the basin hopping step exceeding bounds
                    callback=store_minima,
                    disp=True,
                  )

print(running_data)
print('Time Elapsed:')
print(datetime.datetime.now()-t_start)
print(fit2)
