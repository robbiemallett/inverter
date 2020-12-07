import numpy as np
import pandas as pd
from smrt import make_snowpack, make_model, make_ice_column, PSU
from smrt.interface.iem_fung92_brogioni10 import IEM_Fung92_Briogoni10
from smrt.permittivity.saline_ice import saline_ice_permittivity_pvs_mixing
import itertools
import smrt
import matplotlib.pyplot as plt


def prep_obs():
    signatures, start_dates, end_dates = {}, {}, {}

    for site_number, band, pol in itertools.product([1, 2, 3], ['Ka', 'Ku'], ['VV', 'HH', 'HV']):
        df = pd.read_excel(f'vishnu_real_data/{band}_RS{site_number} Site.xlsx',
                           index_col='Unnamed: 0',
                           sheet_name=pol,
                           parse_dates=True)

        df_resampled = df.resample('3H').mean()

        key = f'{band}_{pol}_RS{site_number}'

        signatures[key] = df_resampled

        start_dates[key] = df_resampled.index[0]
        end_dates[key] = df_resampled.index[-1]

    return (signatures, start_dates, end_dates)

def get_leg_signature(leg):
    df = pd.read_excel('vishnu_real_data/Legs1and2_Time_series_average.xlsx',
                       sheet_name=f'RS{leg} Site')

    return (df)


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
              ):
    """Runs SMRT from geophysical variables and returns a dictionary of results"""

    K_u = 13.575e9
    K_a = 35e9
    freqs = {K_u: 'Ku', K_a: 'Ka'}
    angles = np.arange(0, 51, 5)

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


def plot_mod_and_obs(res, l):

    angles = np.arange(0, 51, 5)

    for key in res.keys():

        if 'Ku' in key:
            color = 'darkblue'
        else:
            color = 'crimson'
        if 'VV' in key:
            ls = '-'
        else:
            ls = '--'

        plt.plot(angles, res[key], marker='s', label=f'{key}_Mod', color=color, ls=ls)

        plt.plot(angles, l[f'{key}_Mean'], marker='^', label=f'{key}_Obs', color=color, ls=ls)

    plt.show()


def cost_fn(res, l):
    rmsds = []
    for key in res.keys():
        model = np.array(res[key])
        obs = np.array(l[f'{key}_Mean'])
        diff = model - obs
        rmsd = np.mean(diff ** 2)
        rmsds.append(rmsd)

    cost = np.sum(rmsds)

    if np.isnan(cost): cost = 1000

    return (cost)


def calculate_cost(params, l):
    trial_res = run_from_params(params)

    cost = cost_fn(trial_res, l)

    return (cost)


def print_params(params):
    params_dict = {'snow_depth': params[0],
                   'ice_thickness': params[1],
                   'ice_salinity': params[2],
                   'ice_density': params[3],
                   'temp': params[4],
                   'snow_CL_e3': params[5],
                   'ice_CL_e3': params[6],
                   'snow_density': params[7],
                   'snow_roughness_rms': params[8],
                   'snow_roughness_CL': params[9],
                   'ice_roughness_rms': params[10],
                   'ice_roughness_CL': params[11],
                   }
    print(params_dict)

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
