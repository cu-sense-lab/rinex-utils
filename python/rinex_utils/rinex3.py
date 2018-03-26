from types import SimpleNamespace
import numpy
from numpy import array, nan, datetime64
from datetime import datetime
import re

# RINEX 3.03
CONSTELLATION_IDS = {
    'G': 'GPS',
    'R': 'GLONASS',
    'E': 'Galileo',
    'S': 'SBAS',
}
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

def parse_RINEX3_header(lines):
    '''
    ------------------------------------------------------------
    Given list of lines corresponding to the header of a RINEX 2
    file, parses the header of the file and returns a namespace
    containing the header information.
    
    Input
    -----
    `lines` -- lines corresponding to RINEX header
    
    Output
    ------
    namespace containing RINEX header information
    '''
    header = SimpleNamespace()
    header.system_obs_types = {}
    header.comments = []
    lines = iter(lines)
    try:
        while True:
            line = next(lines)
            header_label = line[60:].strip()
            if header_label == 'COMMENT':
                header.comments.append(line[0:60])
            elif header_label == 'RINEX VERSION / TYPE':
                header.format_version = line[0:20].strip()
                header.observation_type = line[20:40].strip()
                header.sat_systems = line[40:60].strip()
            elif header_label == 'PGM / RUN BY / DATE':
                header.file_creation_program = line[0:20].strip()
                header.file_creation_agency = line[20:40].strip()
                header.file_creation_epoch = datetime.strptime(line[40:55].strip(), '%Y%m%d %H%M%S')
            elif header_label == 'MARKER NAME':
                header.marker_name = line[0:60].strip()
            elif header_label == 'MARKER NUMBER':
                header.marker_number = line[0:60].strip()
            elif header_label == 'OBSERVER / AGENCY':
                header.observer = line[0:20].strip()
                header.agency = line[20:60].strip()
            elif header_label == 'REC # / TYPE / VERS':
                header.receiver_number = line[0:20].strip()
                header.receiver_type = line[20:40].strip()
                header.receiver_version = line[40:60].strip()
            elif header_label == 'ANT # / TYPE':
                header.antenna_number = line[0:20].strip()
                header.antenna_type = line[20:40].strip()
            elif header_label == 'APPROX POSITION XYZ':
                header.approx_position_xyz = \
                    (float(line[0:14]), float(line[14:28]), float(line[28:42]))
            elif header_label == 'SYS / # / OBS TYPES':
                system_letter = line[0:3].strip()
                number_of_obs = int(line[3:6])
                obs = line[6:60].split()
                if system_letter not in header.system_obs_types.keys():
                    header.system_obs_types[system_letter] = []
                header.system_obs_types[system_letter] += obs
                number_of_obs -= len(obs)
                # Use continuation line(s) for more than 13 observation descriptors
                while number_of_obs > 0:
                    line = next(lines)
                    assert(line[60:].strip() == 'SYS / # / OBS TYPES')
                    obs = line[6:60].split()
                    header.system_obs_types[system_letter] += obs
                    number_of_obs -= len(obs)
            elif header_label == 'SIGNAL STRENGTH UNIT':
                header.signal_strength_unit = line[0:60].strip()
            elif header_label == 'INTERVAL':
                header.interval = float(line[0:60].strip())
            elif header_label == 'TIME OF FIRST OBS':
                header.time_of_first_obs = line[0:60].strip()
            elif header_label == 'TIME OF LAST OBS':
                header.time_of_last_obs = line[0:60].strip()
            elif header_label == 'RCV CLOCK OFFS APPL':
                header.rcv_clock_offs_appl = line[0:60].strip()
            elif header_label == 'SYS / PHASE SHIFT':
                if not hasattr(header, 'phase_shifts'):
                    header.phase_shifts = {}
                system_letter = line[0:1]
                if system_letter not in header.phase_shifts.keys():
                    header.phase_shifts[system_letter] = {}
                signal_id = line[2:5]
                shift = float(line[6:15])
                header.phase_shifts[system_letter][signal_id] = shift
            elif header_label == 'GLONASS SLOT / FRQ #':
                pass
            elif header_label == 'LEAP_SECONDS':
                pass
    except StopIteration:
        pass
    return header

def parse_RINEX3_obs(lines, system_obs_types):
    '''
    ------------------------------------------------------------
    Given list of lines corresponding to the observations of a
    RINEX 3 file, parses the observation epochs and returns a 
    namespace containing the observations for each epoch.
    
    Input
    -----
    `lines` -- lines corresponding to RINEX 3 observation epochs
    `header` -- namespace containing RINEX 3 file header
        information (see `parse_RINEX3_header`)
    
    Output
    ------
    namespace containing RINEX 3 observations
    '''
    
    lines = iter(lines)
    epoch_index = 0
    data = {}  # <sat_id>: {'index': [<5, 6, ...>], <obs_id>: [<values...>]}
    time = []
    try:
        while True:
            # at each epoch, the two-digit year, month, day, hour, minute, and seconds
            # of the measurement epoch are specified, along with the number and ids of
            # the satellites whose measurements are given
            line = next(lines)
            assert(line[0] == '>')
            year = int(line[2:6])
            month = int(line[7:9])
            day = int(line[10:12])
            hour = int(line[13:15])
            minute = int(line[16:18])
            seconds = float(line[19:29])
            microseconds = int(1e6 * (seconds % 1))
            seconds = int(seconds)
            dt = datetime64(datetime(year, month, day, hour, minute, seconds, microseconds))
            time.append(dt)
            flag = int(line[30:32])
            num_sats = int(line[32:35])
            for i in range(num_sats):
                line = next(lines)
                sat_id = line[0:3]
                system_letter = sat_id[0]
                obs_types = system_obs_types[system_letter]
                if sat_id not in data.keys():
                    data[sat_id] = {'index': []}
                    for obs_type in obs_types:
                        data[sat_id][obs_type] = []
                # after the first three characters, should 
                # have 16 * num_obs chars to digest all within
                # one line -- so append spaces at end to reach
                num_chars_to_digest = len(obs_types) * 16
                line = line[3:]
                line += ' ' * (num_chars_to_digest - len(line))
                for j, obs_type in enumerate(obs_types):
                    obs_val = nan
                    obs_str = line[j * 16:(j + 1) * 16].strip()
                    if obs_str != '':
                        obs_val = float(obs_str)
                    data[sat_id][obs_type].append(obs_val)
                data[sat_id]['index'].append(epoch_index)
            epoch_index += 1
    except StopIteration:
        pass
    return data, time

def transform_values_from_RINEX3_obs(data):
    '''
    --------------------------------------------------------
    Given the data dict parsed from RINEX 3 observation
    file, converts data to format:
        {<sat_id>: {<signal_id>: {<obs_id>: ndarray}}}
    
    Returns converted data dict.
    '''
    new_data = {}
    for sat_id in data.keys():
        new_data[sat_id] = {}
        system_letter = sat_id[0]
        constellation = CONSTELLATION_IDS[system_letter]
        obs_datatypes = OBSERVATION_DATATYPES[constellation]
        for obs_id in data[sat_id].keys():
            if obs_id == 'index':
                new_data[sat_id]['index'] = array(data[sat_id]['index'])
                continue
            val_arr = array(data[sat_id][obs_id])
            if numpy.all(numpy.isnan(val_arr)):
                continue
            obs_type = obs_datatypes[obs_id[:2]]
            sig_id, obs_name = obs_type['signal'], obs_type['name']
            if sig_id not in new_data[sat_id].keys():
                new_data[sat_id][sig_id] = {}
            new_data[sat_id][sig_id][obs_name] = array(data[sat_id][obs_id])
    return new_data

def parse_RINEX3_obs_file(filepath):
    '''
    --------------------------------------------------------
    Given the filepath to a RINEX 3 observation file, parses
    and returns header and observation data.
    
    Input
    -----
    `filepath` -- filepath to RINEX observation file

    Output
    ------
    `header, obs_data, (obs_time)` where `header` is a
        namespace containing the parsed header information
        and `obs_data` is a namespace containing the
        observation data in the format:
            data.observations = {
                <sat_id>: namespace(index=ndarray, signals={
                                <sig_id>: namespace(<obs_name>=ndarray)}
                            )
                },
            data.time = ndarray
    '''
    with open(filepath, 'r') as f:
        lines = list(f.readlines())
    for i, line in enumerate(lines):
        if line.find('END OF HEADER') >= 0:
            break
    header_lines = lines[:i + 1]
    obs_lines = lines[i + 1:]
    header = parse_RINEX3_header(header_lines)
    if not hasattr(header, 'system_obs_types'):
        raise Exception('RINEX header must contain `SYS / # / OBS TYPES` and `header` namespace from `parse_RINEX3_header` must contain corresponding dictionary `system_obs_types`')
    obs_data, time = parse_RINEX3_obs(obs_lines, header.system_obs_types)
    obs_data = transform_values_from_RINEX3_obs(obs_data)
    observations = {'time': time, 'satellites': obs_data}
    return header, obs_data

