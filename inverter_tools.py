import numpy as np
import pandas as pd
from smrt import make_snowpack, make_model, make_ice_column, PSU
from smrt.interface.iem_fung92_brogioni10 import IEM_Fung92_Briogoni10
from smrt.permittivity.saline_ice import saline_ice_permittivity_pvs_mixing
import itertools
import smrt
import matplotlib.pyplot as plt

def get_initial_bounds():
    initial_bounds = [(0.08, 0.6),  # Snow Depth
                      (0.6, 2.5),  # Ice Thickness
                      (0.05, 3),  # Ice Salinity
                      (790, 920),  # Ice Density
                      (255, 270),  # Temperature
                      (0.1, 0.4),  # Snow MCL
                      (0.1, 1),  # Ice MCL
                      (250, 400),  # Snow Density
                      #                  (0,1), # Snow Salinity
                      (0.3, 1.5),  # Snow RMS
                      (8, 120),  # Snow RCL
                      (0.1, 2.3),  # Ice RMS
                      (10, 150)]  # Ice RCL

    return(initial_bounds)


def CL_parse(arguments):

    """ Parses input from the command line

    When a python script is called from the command line, arguments to the call can be extracted from sys.argsv. The
    first argument in all of these calls is 'python'. This model is run on high performance machines via calls from
    the command line (organised with a job script).
    Calls from the command line should specifiy whether the machine is an hpc (with -hpc flag), and the tracks for
    the job to run. To specify the tracks, the first argument passed should be the start track (e.g. track no 200),
    the end track (e.g. 60,200), and the step (e.g. 1000). Such arguments would mean that the job will run tracks
    200, 1200, 2200 etc.

    Args:
        arguments: the arguments given in the command line.

    Returns:
        A dictionary with info on the computer type and which tracks the job should run.

    """

    return_dict = {'task_id':arguments[1],
                   'niter':int(arguments[2]),
                   'hpc':('-hpc' in arguments)}

    return(return_dict)

def prep_obs(path_to_obs,resampler='3H',interpolate=False):
    signatures, start_dates, end_dates = {}, {}, {}

    for site_number, band, pol in itertools.product([1, 2, 3], ['Ka', 'Ku'], ['VV', 'HH', 'HV']):
        df = pd.read_excel(f'{path_to_obs}/{band}_RS{site_number} Site.xlsx',
                           index_col='Unnamed: 0',
                           sheet_name=pol,
                           parse_dates=True)

        df_resampled = df.resample(resampler).mean()

        key = f'{band}_{pol}_RS{site_number}'

        if interpolate:
            signatures[key] = df_resampled.interpolate(method='linear')
        else:
            signatures[key] = df_resampled

        start_dates[key] = df_resampled.index[0]
        end_dates[key] = df_resampled.index[-1]

    return (signatures, start_dates, end_dates)

# To delete

# def get_leg_signature(leg,path_to_obs):
#     df = pd.read_excel(f'{path_to_obs}/Legs1and2_Time_series_average.xlsx',
#                        sheet_name=f'RS{leg} Site')
#
#     return (df)




def check_guess_in_bounds(initial_guess, initial_bounds):
    for g, b in zip(initial_guess, initial_bounds):
        if (g < b[0]) or (g > b[1]):
            raise

    return (0)


def run_model(snow_depth,
              ice_thickness,
              ice_salinity,
              ice_density,
              temp,
              snow_CL_e3,
              ice_CL_e3,
              snow_density,
              snow_sal,
              snow_roughness_rms,
              snow_roughness_CL,
              ice_roughness_rms,
              ice_roughness_CL,
              angles= np.arange(0, 51, 5),
              ):
    """Runs SMRT from geophysical variables and returns a dictionary of results"""

    K_u = 13.575e9
    K_a = 35e9
    freqs = {K_u: 'Ku', K_a: 'Ka'}

    snow_air_interface = IEM_Fung92_Briogoni10(roughness_rms=snow_roughness_rms * 1e-3,
                                               corr_length=snow_roughness_CL * 1e-3)

    snow_ice_interface = IEM_Fung92_Briogoni10(roughness_rms=ice_roughness_rms * 1e-3,
                                               corr_length=ice_roughness_CL * 1e-3)

    ice_column = make_ice_column(ice_type='multiyear',
                                 thickness=[ice_thickness],
                                 temperature=temp,
                                 brine_inclusion_shape='needles',
                                 corr_length=ice_CL_e3 / 1000,
                                 density=ice_density,
                                 salinity=ice_salinity * PSU,
                                 microstructure_model='exponential',
                                 add_water_substrate='ocean',
                                 ice_permittivity_model=saline_ice_permittivity_pvs_mixing,
                                 interface=snow_ice_interface,

                                 )

    snowpack = make_snowpack(thickness=[snow_depth],
                             microstructure_model="exponential",
                             density=snow_density,
                             temperature=temp,
                             corr_length=snow_CL_e3 / 1000,
                             salinity=snow_sal,
                             #                              ice_permittivity_model = saline_snow_permittivity_geldsetzer09,
                             interface=snow_air_interface,
                             )

    medium = snowpack + ice_column

    sensor = smrt.sensor.active([K_u, K_a], angles, polarization_inc=['H'], polarization=['V', 'H'])

    m = make_model("iba", "dort")

    res = m.run(sensor, medium)

    results = {}

    for pol_inc, pol, freq in itertools.product(['H'], ['V', 'H'], [K_a, K_u]):
        # Turn SMRT results object into a sliced dataframe

        s_res = res.sigma_dB_as_dataframe(polarization_inc=pol_inc,
                                          polarization=pol,
                                          frequency=freq)

        # Process slice into dictionary

        results[f'{freqs[freq]}_{pol_inc}{pol}'] = np.array(s_res['sigma'])

    return (results)

def get_obs_dict(start_date='2019-11-29 09:00:00',
                 end_date='2019-12-01 06:00:00',
                 site_no=2,
                 path_to_obs='../vishnu_real_data'):

    signatures, start_dates, end_dates = prep_obs(path_to_obs)

    obs_dict = {}
    for i, j in itertools.product(['Ku', 'Ka'], ['VV', 'HV', 'HH']):
        df = signatures[f'{i}_{j}_RS{site_no}'][str(start_date):str(end_date)]

        col_means = [np.nanmean(df[column]) for column in df.columns]

        obs_dict[f'{i}_{j}_Mean'] = col_means

    return(obs_dict)


def plot_mod_and_obs(mod,
                     obs,
                     legend=False,
                     angles = np.arange(0, 51, 5),
                     shade_cost=True,
                     show=True):

    fig, ax = plt.subplots(1,1,figsize=(8,5))

    for key in mod.keys():

        if 'Ku' in key:
            color = 'darkblue'
        else:
            color = 'crimson'
        if ('VV' in key) or ('HH' in key):
            ls = '-'
        else:
            ls = '--'
        ax.set_ylabel('Backscatter (dB)', fontsize='x-large')
        ax.set_xlabel(r'Inc. Angle ($^{\circ}$)', fontsize='x-large')
        ax.plot(angles, mod[key], marker='s', label=f'{key[:2]} {key[3:5]} Mod', color=color, ls=ls)

        ax.plot(angles, obs[f'{key}_Mean'], marker='^', label=f'{key[:2]} {key[3:5]} Obs', color=color, ls=ls)

        if shade_cost:
            cost = np.round(cost_fn(mod,obs),decimals=2)
            ax.annotate(f'Cost: {cost}',xy=(0.99,0.95),xycoords='axes fraction',
                        ha='right',fontsize='large')
            ax.fill_between(angles, mod[key], obs[f'{key}_Mean'],color='grey',alpha = 0.3)



    if legend:
        plt.legend(fontsize='x-large',
                  loc='lower left',
                  bbox_to_anchor=[1, 0]
                  )

    if show: plt.show()

    return(fig)




def cost_fn(res, l):
    rmsds = []
    for key in res.keys():
        model = np.array(res[key])
        obs = np.array(l[f'{key}_Mean'])
        diff = model - obs
        rmsd = np.mean(diff ** 2)
        rmsds.append(rmsd)

    cost = np.sum(rmsds)

    for key in res:
        if np.isnan(res[key]).any():
            cost = 1000

    if np.isnan(cost): cost = 1000

    return (cost)


def calculate_cost(params, l):

    try:
        trial_res = run_from_params(params)

        cost = cost_fn(trial_res, l)
    except Exception as e:
        print(e)
        cost = 1000

    return (cost)


def print_params(params):
    params_dict = {'snow_depth': np.round(params[0],2),
                   'ice_thickness': np.round(params[1],2),
                   'ice_salinity': np.round(params[2],2),
                   'ice_density': np.round(params[3],2),
                   'temp': np.round(params[4],2),
                   'snow_CL_e3': np.round(params[5],2),
                   'ice_CL_e3': np.round(params[6],2),
                   'snow_density': np.round(params[7],2),
                   'snow_roughness_rms': np.round(params[8],2),
                   'snow_roughness_CL': np.round(params[9],2),
                   'ice_roughness_rms': np.round(params[10],2),
                   'ice_roughness_CL': np.round(params[11],2),
                   }

    return (params_dict)


def run_from_params(params):

    trial_res = run_model(snow_depth=params[0],
                          ice_thickness=params[1],
                          ice_salinity=params[2],
                          ice_density=params[3],
                          temp=params[4],
                          snow_CL_e3=params[5],
                          ice_CL_e3=params[6],
                          snow_density=params[7],
                          snow_sal=0,
                          snow_roughness_rms=params[8],
                          snow_roughness_CL=params[9],
                          ice_roughness_rms=params[10],
                          ice_roughness_CL=params[11],
                          )

    return (trial_res)


def plot_fit(fit, l):
    tuned_res = run_from_params(fit.x)
    plot_mod_and_obs(tuned_res, l)

def check_valid_bounds(params, bounds):
    for param, bound in zip(params, bounds):
        if (bound[0] > param) or (param > bound[1]):
            return (False)

    return (True)
