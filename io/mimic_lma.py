import numpy as np
import pandas as pd
import xarray as xr

# from glmtools.io.glm import fix_unsigned
def fix_unsigned(arg):
    return arg

# from lmatools.io.LMA_h5_file import LMAh5Collection

# h5LMAfiles=('/data/20130606/LMA/LYLOUT_130606_032000_0600.dat.flash.h5',)

# h5s = LMAh5Collection(h5LMAfiles, base_date=panels.basedate, min_points=10)    
# for events, flashes in h5s: # get a stream of events, flashes 
#     print events.dtype
#     print flashes.dtype

def sec_since_basedate(t64, basedate):
    """ given a numpy datetime 64 object, and a datetime basedate, 
        return seconds since basedate"""
    
    t_series = pd.Series(t64) - basedate
    t = np.fromiter((dt.total_seconds() for dt in t_series), dtype='float64')
    return t

def _fake_lma_from_glm(flash_data, basedate):
    """ flash_data is an xarray record of flashes, groups, and events for a 
        single lightning flash.
    
        flash_data can be generated with the mimic_lma_dataset in this module.
        Crucially, that funciton uses the GLMDataset object to add flash IDs
        to the flash_data structure, as below:
        event_parent_flash_id = glm.flash_id_for_events(flash_data)
        flash_data['event_parent_flash_id']=xr.DataArray(event_parent_flash_id, dims=[glm.ev_dim])
    """
    # These are the dtypes in the LMA HDF5 data files
    event_dtype=[('flash_id', '<i4'), 
                 ('alt', '<f4'), 
#                  ('charge', 'i1'), ('chi2', '<f4'), ('mask', 'S4'), ('stations', 'u1'),
                 ('lat', '<f4'), ('lon', '<f4'), ('time', '<f8'),
                 ('power', '<f4'), ]
    flash_dtype=[('area', '<f4'),  ('total_energy', '<f4'), 
                 #('volume', '<f4'), 
                 ('specific_energy', '<f4'), 
                 ('ctr_lat', '<f4'), ('ctr_lon', '<f4'), 
                 ('ctr_alt', '<f4'), 
                 ('start', '<f8'), ('duration', '<f4'), 
                 ('init_lat', '<f4'), ('init_lon', '<f4'), 
                 ('init_alt', '<f4'),# ('init_pts', 'S256'), 
                 ('flash_id', '<i4'),  ('n_points', '<i2'),  ]

    
    flash_np = np.empty_like(flash_data.flash_id.data, dtype=flash_dtype)
    event_np = np.empty_like(flash_data.event_id.data, dtype=event_dtype)

    
    # for each event get the group id
    # for each group id get the flash id

    
    event_np['flash_id'] = flash_data.event_parent_flash_id.data
    # Doesn't work for more than one flash in the data table.
    # event_np['flash_id'] = flash_data.event_parent_flash_id.data

#     ev_lats, ev_lons = fix_event_locations(flash_data.event_lat, flash_data.event_lon, is_xarray=True)
    event_np['lat'] = fix_unsigned(flash_data.event_lat) # ev_lats
    event_np['lon'] = fix_unsigned(flash_data.event_lon)
    t_event = sec_since_basedate(flash_data.event_time_offset.data, basedate)
    event_np['time'] = t_event
    event_np['power'] = fix_unsigned(flash_data.event_energy) 

    flash_np['area'] = fix_unsigned(flash_data.flash_area)
    flash_np['total_energy'] = fix_unsigned(flash_data.flash_energy)
    flash_np['ctr_lon'] = flash_data.flash_lon.data
    flash_np['ctr_lat'] = flash_data.flash_lat.data
    flash_np['init_lon'] = flash_data.flash_lon.data
    flash_np['init_lat'] = flash_data.flash_lat.data
    t_start = sec_since_basedate(flash_data.flash_time_offset_of_first_event.data, basedate)
    t_end = sec_since_basedate(flash_data.flash_time_offset_of_last_event.data, basedate)
    flash_np['start'] = t_start
    flash_np['duration'] = t_end-t_start
    flash_np['flash_id'] = flash_data.flash_id.data
    flash_np['n_points'] = flash_data.number_of_events.shape[0]
    
    # Fake the altitude data
    event_np['alt'] = 0.0
    flash_np['ctr_alt'] = 0.0
    flash_np['init_alt'] = 0.0
    
    # Fake the specific energy data
    flash_np['specific_energy'] = 0.0
    
    return event_np, flash_np



def mimic_lma_dataset(glm, basedate, flash_ids=None, lon_range=None, lat_range=None):
    """ Mimic the LMA data structure from GLM """
    
    if ((lon_range is not None) | (lat_range is not None)):
        flash_data = glm.lonlat_subset(lon_range=lon_range, lat_range=lat_range)

    elif flash_ids is not None:
        flash_data = glm.get_flashes(flash_ids)
    else:
        flash_data = glm.dataset
            
    event_parent_flash_id = glm.flash_id_for_events(flash_data)
    flash_data['event_parent_flash_id']=xr.DataArray(event_parent_flash_id, dims=[glm.ev_dim])
    events, flashes = _fake_lma_from_glm(flash_data, basedate)
    return events, flashes