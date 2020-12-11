# SMRT Inversion

The backscatter properties of snow on sea ice were monitored at Ka- and Ku-bands during the MOSAiC Expedition. These were montitored in the co- and cross-polarised configuration at a variety of angles.

SMRT is a microwave transfer model that takes in geophysical parameters and can output backscatter values.

The goal of this code is to 'invert' this modelling flow. That is to say, we want a machine that takes in backscatter signatures and returns geophysical parameters. 

It is also highly desirable to link time-evolution in the backscatter signature of snow to time-evolution in its geophysical parameters (via the inverse model).

## Forward-SMRT Setup

We set up SMRT in forward-mode to output the backscatter values measured by the Ku-Ka. This consists of four 'channels': Ka- and Ku-band in co- and cross-polarisation. The backscatter for all four channels was measured over a range of incidence angles (spaced at five-degrees) from 0 to 50 degrees (measured from the vertical).

SMRT was configured as a two-layer system with an ocean substrate. The snow-air and snow-ice interfaces were modelled using the IEM with independent roughness characteristics (each interface is characterised by an RMS height and a height anomaly correlation length). 

We then created a set of boundary conditions, defining a finite-volume parameter-space. This parameter-space is currently twelve-dimensional, with each dimension corresponding to a range of a certain parameter such as snow depth. The physical state of a snow-sea-ice input to forward-SMRT is therefore uniquely relatable to a single point in this high-dimensional parameter-space.

## Search-Mode (time independent)

The 'search-mode' of the inversion searches the parameter space for a set of SMRT inputs that match a given backscatter signature (taken at a single time). The 'best match' is quantified by a cost function, which is to be minimised. This global minimisation problem is handled by the SciPy Basinhopping algorithm. The local minimisation algorithm within this is configurable - so far I've experimented with SLSQP and L-BFGS-B. 

## Track-Mode (time dependent)

The 'track-mode' of the inversion is designed to assimilate the evolution of the backscatter signature and output the corresponding evolution of the geophysical parameters.

This is done by first operating in 'Search-Mode' to find the best possible match to the first backscatter signature in the timeseries. We then assume that the backscatter evolves slowly and smoothly - this is important. We then use the geophysical parameters (x<sub>0</sub>,y<sub>0</sub>,z<sub>0</sub>) that correspond to the backscatter signature's cost minimum at t=t<sub>0</sub> as an initial guess for the position of the cost-minimum for the backscatter signature at t=t<sub>1</sub>. We then run a local-minimisation algorithm to update the position of this minimum based on the guess, thus finding (x<sub>1</sub>,y<sub>1</sub>,z<sub>1</sub>). To summarise, we iteratively update the cost function, and iteratively track the position of the minimum of the *same basin* through time. The movement of the minimum in the parameter-space corresponds to the physical evolution of the snowpack's properties. By staying in the same basin, we avoid the need to search the whole parameter space for the lowest minimum at every timestep. Instead, we can just do a local search. 
