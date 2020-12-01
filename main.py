import datetime
from inverter_classes import MyBounds, MyTakeStep
from inverter_tools import run_model, calculate_cost, get_leg_signature
from scipy.optimize import basinhopping
import scipy
print(scipy.__version__)

res = run_model(snow_depth=0.25,
                ice_thickness=0.7,
                ice_salinity=0.5,
                ice_density=830,
                temp=260,
                snow_CL_e3=0.3,
                ice_CL_e3=0.34,
                snow_density=350,
                snow_sal=0,
                snow_roughness_rms=0.5,
                snow_roughness_CL=20,
                ice_roughness_rms=2.1,
                ice_roughness_CL=120)

initial_guess = [0.25,  # Snow Depth
                 0.7,  # Ice Thickness
                 0.5,  # Ice Salinity
                 830,  # Ice Density
                 260,  # Temperature
                 0.3,  # Snow MCL
                 0.34,  # Ice MCL
                 350,  # Snow Density
                 #                  0, # Snow Salinity
                 0.5,  # Snow RMS
                 20,  # Snow RCL
                 2.1,  # Ice RMS
                 120]  # Ice RCL

initial_bounds = [(0.2, 0.3),  # Snow Depth
                  (0.6, 1.5),  # Ice Thickness
                  (0.1, 3),  # Ice Salinity
                  (790, 920),  # Ice Density
                  (255, 270),  # Temperature
                  (0.1, 0.4),  # Snow MCL
                  (0.1, 1),  # Ice MCL
                  (250, 400),  # Snow Density
                  #                  (0,1), # Snow Salinity
                  (0.3, 1.5),  # Snow RMS
                  (8, 120),  # Snow RCL
                  (0.1, 2.2),  # Ice RMS
                  (10, 150)]  # Ice RCL


l = get_leg_signature(3)

running_data = []

def store_minima(x, f, accepted):
    running_data.append((x, f))

t_start = datetime.datetime.now()
fit2 = basinhopping(calculate_cost,
                    x0 = initial_guess,
                    stepsize=1,
                    niter=5,
                    minimizer_kwargs={
                        'method':'SLSQP',
                        'args':(l,), # Passes through the observations for the cost function calculation
                        'bounds':initial_bounds, # Stops the local minimizer exceeding bounds
                                        },
                    take_step=MyTakeStep(initial_bounds), # Ensures that parameter-space is evenly stepped through
                    accept_test=MyBounds(initial_bounds), # Stops the basin hopping step exceeding bounds
                    callback=store_minima,
                    disp=True,
                    niter_success=10,
                  )

print(running_data)
print('Time Elapsed:')
print(datetime.datetime.now()-t_start)
print(fit2)