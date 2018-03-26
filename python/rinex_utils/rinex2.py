from types import SimpleNamespace
import numpy
from numpy import array, nan, datetime64
from datetime import datetime
import re

# RINEX 2.10 - 2.11
CONSTELLATION_IDS = {
    'G': 'GPS',
    'R': 'GLONASS',
    'E': 'Galileo',
    'S': 'SBAS',
}
# RINEX version 2 does not distinguish tracking modes (added in RINEX V3)
# As such, for GPS, simple signal names L1, L2, L5 are used
OBSERVATION_DATATYPES = {
    'GPS': {
        'C1': {'signal': 'L1', 'name': 'pseudorange'},
        'P1': {'signal': 'L1', 'name': 'pseudorange'},
        'L1': {'signal': 'L1', 'name': 'carrier'},
        'D1': {'signal': 'L1', 'name': 'doppler'},
        'S1': {'signal': 'L1', 'name': 'snr'},
        'C2': {'signal': 'L2', 'name': 'pseudorange'},
        'P2': {'signal': 'L2', 'name': 'pseudorange'},
        'L2': {'signal': 'L2', 'name': 'carrier'},
        'D2': {'signal': 'L2', 'name': 'doppler'},
        'S2': {'signal': 'L2', 'name': 'snr'},
        'C5': {'signal': 'L5', 'name': 'pseudorange'},
        'P5': {'signal': 'L5', 'name': 'pseudorange'},
        'L5': {'signal': 'L5', 'name': 'carrier'},
        'D5': {'signal': 'L5', 'name': 'doppler'},
        'S5': {'signal': 'L5', 'name': 'snr'},
    },
    'GLONASS': {
        'C1': {'signal': 'L1', 'name': 'pseudorange'},
        'P1': {'signal': 'L1', 'name': 'pseudorange'},
        'L1': {'signal': 'L1', 'name': 'carrier'},
        'D1': {'signal': 'L1', 'name': 'doppler'},
        'S1': {'signal': 'L1', 'name': 'snr'},
        'C2': {'signal': 'L2', 'name': 'pseudorange'},
        'P2': {'signal': 'L2', 'name': 'pseudorange'},
        'L2': {'signal': 'L2', 'name': 'carrier'},
        'D2': {'signal': 'L2', 'name': 'doppler'},
        'S2': {'signal': 'L2', 'name': 'snr'},
    },
    'Galileo': {
        'C1': {'signal': 'E1', 'name': 'pseudorange'},
        'L1': {'signal': 'E1', 'name': 'carrier'},
        'D1': {'signal': 'E1', 'name': 'doppler'},
        'S1': {'signal': 'E1', 'name': 'snr'},
        'C5': {'signal': 'E5a', 'name': 'pseudorange'},
        'L5': {'signal': 'E5a', 'name': 'carrier'},
        'D5': {'signal': 'E5a', 'name': 'doppler'},
        'S5': {'signal': 'E5a', 'name': 'snr'},
        'C7': {'signal': 'E5b', 'name': 'pseudorange'},
        'L7': {'signal': 'E5b', 'name': 'carrier'},
        'D7': {'signal': 'E5b', 'name': 'doppler'},
        'S7': {'signal': 'E5b', 'name': 'snr'},
        'C8': {'signal': 'E5ab', 'name': 'pseudorange'},
        'L8': {'signal': 'E5ab', 'name': 'carrier'},
        'D8': {'signal': 'E5ab', 'name': 'doppler'},
        'S8': {'signal': 'E5ab', 'name': 'snr'},
        'C6': {'signal': 'E6', 'name': 'pseudorange'},
        'L6': {'signal': 'E6', 'name': 'carrier'},
        'D6': {'signal': 'E6', 'name': 'doppler'},
        'S6': {'signal': 'E6', 'name': 'snr'},
    },
    'SBAS': {
        'C1': {'signal': 'L1', 'name': 'pseudorange'},
        'L1': {'signal': 'L1', 'name': 'carrier'},
        'D1': {'signal': 'L1', 'name': 'doppler'},
        'S1': {'signal': 'L1', 'name': 'snr'},
        'C5': {'signal': 'L5', 'name': 'pseudorange'},
        'L5': {'signal': 'L5', 'name': 'carrier'},
        'D5': {'signal': 'L5', 'name': 'doppler'},
        'S5': {'signal': 'L5', 'name': 'snr'},
    },
}

def parse_RINEX2_header(lines):
    '''
    Given list of lines corresponding to the header of a RINEX file, parses
    the header of the file and returns a namespace containing the header information.
    
    Input
    -----
    `lines` -- lines corresponding to RINEX header
    
    Output
    ------
    namespace containing RINEX header information
    '''
    header = SimpleNamespace()
    lines = iter(lines)
    try:
        while True:
            line = next(lines)
            if line[60:].strip() == 'RINEX VERSION / TYPE':
                header.version = line[:20].strip()
                header.type = line[20:60].strip()
            elif line[60:].strip() == 'PGM / RUN BY / DATE':
                header.program = line[:20].strip()
                header.run_by = line[20:40].strip()
                header.date = line[40:60].strip()
            elif line[60:].strip() == 'MARKER NAME':
                header.marker_name = line[:60].strip()
            elif line[60:].strip() == 'MARKER NUMBER':
                header.marker_number = line[:60].strip()
            elif line[60:].strip() == 'OBSERVER / AGENCY':
                header.observer = line[:20].strip()
                header.agency = line[20:60].strip()
            elif line[60:].strip() == 'REC # / TYPE / VERS':
                header.receiver_number = line[:20].strip()
                header.receiver_type = line[20:40].strip()
                header.receiver_version = line[40:60].strip()
            elif line[60:].strip() == 'ANT # / TYPE':
                header.antenna_number = line[:20].strip()
                header.antenna_type = line[20:60].strip()
            elif line[60:].strip() == 'APPROX POSITION XYZ':
                header.approximate_position_xyz = line[:60].strip()
            elif line[60:].strip() == 'ANTENNA: DELTA H/E/N':
                header.delta_hen = line[:60].strip()
            elif line[60:].strip() == 'APPROX POSITION XYZ':
                header.approximate_position_xyz = line[:60].strip()
            elif line[60:].strip() == 'WAVELENGTH FACT L1/2':
                header.wavelength_fact_l12 = line[:60].strip()
            elif line[60:].strip() == 'APPROX POSITION XYZ':
                header.approximate_position_xyz = line[:60].strip()
            elif line[60:].strip() == 'TIME OF FIRST OBS':
                header.time_of_first_obs = line[:60].strip()
            elif line[60:].strip() == '# / TYPES OF OBSERV':
                n_obs_str = line[:10].strip()
                if n_obs_str:
                    header.n_obs = int(n_obs_str)
                    header.obs_types = []
                header.obs_types += line[10:60].split()
            elif line[60:].strip() == 'COMMENT':
                pass
    except StopIteration:
        pass
    return header


def parse_RINEX2_obs_data(lines, observations, century=2000, return_time=False):
    '''
    Given `lines` corresponding to the RINEX observation file data (non-header) lines,
    and a list of the types of observations recorded at each epoch, produces a dictionary
    containing the observation time and values for each satellite.
    
    Input
    -----
    `lines` -- data lines from RINEX observation file
    `observations` -- list of the observations reported at each epoch
    
    Output
    ------
    `data` -- dictionary of format:
        {<sat_id>: {'time': [<dt...>], <obs_id>: [<values...>]}}
    `time` -- list of times corresponding to epochs
    '''
    data = {}  # <sat_id>: {'time': [<dt...>], <obs_id>: [<values...>]}
    lines = iter(lines)
    epoch_index = 0
    time = []
    try:
        while True:
            # at each epoch, the two-digit year, month, day, hour, minute, and seconds
            # of the measurement epoch are specified, along with the number and ids of
            # the satellites whose measurements are given
            line = next(lines)
            yy = int(line[:4].strip())
            year = century + yy
            month = int(line[4:7])
            day = int(line[7:10])
            hour = int(line[10:13])
            minute = int(line[13:16])
            seconds = float(line[16:25])
            microseconds = int(1e6 * (seconds % 1))
            seconds = int(seconds)
            dt = datetime64(datetime(year, month, day, hour, minute, seconds, microseconds))
            time.append(dt)
            flag = int(line[25:28])
            num_sats = int(line[29:32])
            # there is space for (80 - 32) / 3 = 16 satellite ids
            # if there are more than 16, then they continue on the next line
            # a general approach is to consume lines until we have determined all sat IDs
            sat_ids = []
            line = line[32:].strip()
            while len(sat_ids) < num_sats:
                sat_ids.append(line[:3].replace(' ', '0'))
                line = line[3:]
                if line == '' and len(sat_ids) < num_sats:
                    line = next(lines)
                    assert(line[:32].strip() == '')
                    line = line.strip()
                    assert(len(line) % 3 == 0)  # sanity check -- each sat ID takes 3 chars
            for sat_id in sat_ids:
                # create new entry if `sat_id` is new
                if sat_id not in data.keys():
                    data[sat_id] = {'index': [], 'time': []}
#                     for obs_id in observations:
#                         data[sat_id][obs_id] = []
                # append time/index first, then append obs values
                data[sat_id]['time'].append(dt)
                data[sat_id]['index'].append(epoch_index)
                # each line of observation values contains up to 5 entries
                # each entry is of width 16, starting at index 0
                num_lines_per_sat = 1 + len(observations) // 5
                line = ''
                for i in range(num_lines_per_sat):
                    line += next(lines).replace('\n', '').ljust(80)
                for i, obs_id in enumerate(observations):
                    val_str = line[16 * i:16 * (i + 1)].strip()
                    if val_str == '':
                        continue
                    val_str = val_str.split()
                    if len(val_str) == 1:
                        val_str = val_str[0]
                    elif len(val_str) == 2:
                        val_str, sig_flag = val_str
                    else:
                        assert(False)  # error
                    try:
                        val = float(val_str)
                    except Exception:
                        val = nan
                    if obs_id not in data[sat_id].keys():
                        data[sat_id][obs_id] = []
                    data[sat_id][obs_id].append(val)
            epoch_index += 1
    except StopIteration:
        pass
    if return_time:
        return data, array(time)
    return data

def transform_values_from_RINEX2_obs(rinex_data):
    '''
    Transforms output from `parse_obs` to more useful format.
    
    Input:
    -------
    `rinex_data` -- Python dictionary with format:
        {<sat_id>: {'time': [<dt...>], <obs_id>: [<values...>]}}
        
    Output:
    -------
    `data` -- namespace containing:
        `satellites` -- dictionary of format {<sat_id>: <namespace>} with
        <namespace> containing time array and signal namespaces.  Each 
        signal namespace contains arrays of any measurements for that 
        corresponding signal.
    '''
    data = {}
    for sat_id, rnx_sat in rinex_data.items():
        if sat_id not in data.keys():
            data[sat_id] = SimpleNamespace(signals={})
        sat = data[sat_id]
        for obs_name, mapping in OBSERVATION_DATATYPES.items():
            if obs_name in rnx_sat.keys():
                signal = mapping['signal']
                if signal not in sat.signals.keys():
                    sat.signals[signal] = SimpleNamespace()
                setattr(sat.signals[signal], mapping['name'], array(rnx_sat[obs_name]))
        if 'time' in rnx_sat.keys():
            sat.time = array(rnx_sat['time'])
        if 'index' in rnx_sat.keys():
            sat.index = array(rnx_sat['index'])
    return data

def parse_RINEX2_obs_file(filepath, return_time=False):
    '''Given the filepath to a RINEX observation file, parses and returns header
    and observation data.
    
    Input
    -----
    `filepath` -- filepath to RINEX observation file
    `return_time` -- (default=False) return the list of times corresponding to epochs

    Output
    ------
    `header, obs_data, (obs_time)` where `header` is a namespace containing the parsed header information
        and `obs_data` is a namespace containing the observation data in the format:
        {<sat_id>: namespace(time=ndarray, signals={<sig_id>: namespace(<obs_name>=ndarray)})}
        `obs_time` only present when `return_time` True -- list of times.
        
        Note: `time` on the satellite namespace is a `numpy.datetime64` object
    '''
    with open(filepath, 'r') as f:
        lines = list(f.readlines())
    for i, line in enumerate(lines):
        if line.find('END OF HEADER') >= 0:
            break
    header_lines = lines[:i + 1]
    obs_lines = lines[i + 1:]
    header = parse_RINEX2_header(header_lines)
    if not hasattr(header, 'obs_types'):
        raise Exception('RINEX header must contain `# / TYPES OF OBS.` and `header` namespace from `parse_parse_RINEX2_header` must contain corresponding list `obs_types`')
    obs_data, obs_time = parse_RINEX2_obs_data(obs_lines, header.obs_types, return_time=True)
    obs_data = transform_values_from_RINEX2_obs(obs_data)
    if return_time:
        return header, obs_data, obs_time
    return header, obs_data
