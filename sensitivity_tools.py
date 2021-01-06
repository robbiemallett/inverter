import numpy as np
from smrt.substrate.reflector_backscatter import make_reflector
from smrt import make_snowpack, make_model, make_ice_column, PSU
from smrt.interface.iem_fung92_brogioni10 import IEM_Fung92_Briogoni10
from smrt.permittivity.saline_ice import saline_ice_permittivity_pvs_mixing
import itertools
import smrt
import matplotlib.pyplot as plt
import inverter_tools


def sensitivity(canonical, variable, bounds, ax=0, show=True, penetration=False):
    trial_dict = canonical.copy()

    for value, marker in zip([bounds[variable][0], bounds[variable][1]], ['x', 'o']):
        trial_dict[variable] = value

        trial_params = [value for value in list(trial_dict.values())]

        run = run_sensitivity_from_params(trial_params,penetration)

        ax = plot_result(run, marker=marker, ax=ax)

    if show: plt.show()

    return (ax)


def run_sensitivity_from_params(params,bb_ref):
    trial_res = run_model_bb(snow_depth=params[0],
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
                          bb_ref=bb_ref,
                          )

    return (trial_res)

def plot_result(res, marker='x', ax=0, show=False):
    angles = np.arange(0, 51, 5)

    if ax == 0:
        fig, ax = plt.subplots(1, 1)

    for key in res.keys():

        if 'Ku' in key:
            color = 'darkblue'
        else:
            color = 'crimson'

        if ('VV' in key) or ('HH' in key):
            ls = '-'
        else:
            ls = '--'
        ax.set_ylabel('Backscatter (dB)', fontsize='x-large')
        ax.set_xlabel('Inc. Angle', fontsize='x-large')
        ax.plot(angles, res[key], marker=marker, label=f'{key}_Mod', color=color, ls=ls)

    if show:
        plt.show()

    return (ax)

def run_model_bb(snow_depth,
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
              bb_ref,
              angles = np.arange(0, 51, 5),
              ):
    """Runs SMRT from geophysical variables and returns a dictionary of results"""

    K_u = 13.575e9
    K_a = 35e9
    freqs = {K_u: 'Ku', K_a: 'Ka'}


    snow_air_interface = IEM_Fung92_Briogoni10(roughness_rms=snow_roughness_rms * 1e-3,
                                               corr_length=snow_roughness_CL * 1e-3)

    snow_ice_interface = IEM_Fung92_Briogoni10(roughness_rms=ice_roughness_rms * 1e-3,
                                               corr_length=ice_roughness_CL * 1e-3)

    # if bb_ref:
    #     ref = make_reflector(temperature=0, specular_reflection=0)
    # else:
    #     ref = None


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
                             # ice_permittivity_model = saline_snow_permittivity_geldsetzer09,
                             interface=snow_air_interface,
                             )

    if bb_ref:
        medium = snowpack
    else:
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

