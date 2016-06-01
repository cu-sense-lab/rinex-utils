import gpstk
import numpy as np
from numpy import zeros, arange, array, nan

def parse_rinex(filepath):
    """
        parses a rinex file, and returns a dictionary containing the data
        gpstk package must be installed
    """
    num_prns = 32
    header, records = gpstk.readRinexObs(filepath)
    N = 0
    for record in records:
        N += 1
    print('There are {0} records'.format(N))
    obs_descriptions = [o.description for o in header.obsTypeList]
    # pick valid MATLAB/Python variable names
    alternate_names = {'C/A-code pseudorange': 'psr_l1',
                       'L2C-code pseudorange': 'psr_l2',
                       'L5C-code pseudorange': 'psr_l5',
                       'L1 Carrier Phase': 'phs_l1',
                       'L2 Carrier Phase': 'phs_l2',
                       'L5 Carrier Phase': 'phs_l5',
                       'Pcode L1 pseudorange': 'psr_l1p',
                       'Pcode L2 pseudorange': 'psr_l2p',
                       'Doppler Frequency L1': 'dopp_l1',
                       'Doppler Frequency L2': 'dopp_l2',
                       'Signal-to-Noise L1': 'snr_l1',
                       'Signal-to-Noise L2': 'snr_l2',
                       'Signal-to-Noise L5': 'snr_l5'
                      }
    header, records = gpstk.readRinexObs(filepath)
    data = {}
    for name in alternate_names.values():
        data[name] = nan * zeros((num_prns, N))  # just GPS satellites
    data['rx_ecef'] = tuple(header.antennaPosition[i] for i in range(3))
    i = 0  # record number, i.e. seconds from start of day (1Hz data)
    for record in records:
        record_dict = record.obs.asdict()
        for sat_id in record_dict.keys():
            prn = sat_id.id
            sat_obs_dict = record_dict[sat_id].asdict()
            for key in sat_obs_dict.keys():
                var_name = alternate_names[key.description]
                data[var_name][prn - 1, i] = sat_obs_dict[key].data
        i += 1
    print('Date: ' + str(header.date))
    print('Collection Interval: '+ str(header.interval) + ' sec')
    
    return data



