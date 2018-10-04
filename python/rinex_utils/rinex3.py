# %load /home/breitsbw/projects/utilities/rinex-utils/python/rinex_utils/rinex3.py
import numpy
from numpy import array, nan, datetime64, isnan
from datetime import datetime

# RINEX 3.03
CONSTELLATION_LETTERS = {
    'G': 'GPS',
    'R': 'GLONASS',
    'E': 'Galileo',
    'J': 'QZSS',
    'C': 'BDS',  # Beidou
    'I': 'IRNSS',
    'S': 'SBAS',
}
OBSERVATION_LETTERS = {
    'C': 'pseudorange',
    'L': 'carrier',
    'D': 'doppler',
    'S': 'cnr',
}

BAND_AND_CHANNEL_MAPPINGS = {
    'GPS': {
        '1' : {'band':'L1', 'frequency':1575.42,
             'channel_ids':{
                 'C': 'C/A',
                 'S': 'L1C(D)',
                 'L': 'L1C(P)',
                 'X': 'L1C (D+P)',
                 'P': 'P (AS off)',
                 'W': 'Z-tracking and similar(AS on)',
                 'Y': 'Y',
                 'M': 'M',
                 'N': 'codeless'
             }
            },
        '2' : {'band':'L2', 'frequency':1227.60,
                'channel_ids':{
                    'C':'C/A',
                    'D':'L1(C/A)+(P2-P1)(semi-codeless)',
                    'S':'L2C (M)',
                    'L':'L2C (L)',
                    'X':'L2C (M+L)',
                    'P':'P (AS off)',
                    'W':'Z-tracking and similar(AS on)',
                    'Y':'Y',
                    'M':'M',
                    'N':'codeless'
                }
              },
         '5' : {'band':'L5', 'frequency':1176.45,
                'channel_ids':{
                    'I': 'I',
                    'Q': 'Q',
                    'X': 'I+Q'
                }
               }
    },
    'GLONASS':{
        '1' : {'band':'G1', 'frequency':lambda k: 1602+k*(9/16),
                 'channel_ids':{
                     'C': 'C/A',
                     'P': 'P'
                 }
              },
        '2' : {'band':'G2', 'frequency':lambda k: 1246+k*716,
             'channel_ids':{
                 'C': 'C/A(GLONASS M)',
                 'P': 'P'
             }
            },
        '3' : {'band':'G3', 'frequency':1202.025,
             'channel_ids':{
                 'I': 'I',
                 'Q': 'Q',
                 'X': 'I+Q'
             }
            }
    },
     'Galileo': {
        '1': {'band': 'E1', 'frequency': 1575.42,
             'channel_ids': {
                 'A': 'A PRS',
                 'B': 'B I/NAV OS/CS/SoL',
                 'C': 'C no data',
                 'X': 'B+C',
                 'Z': 'A+B+C',
             }
            },
        '5': {'band': 'E5a', 'frequency': 1176.45,
             'channel_ids': {
                 'I': 'I F/NAV OS',
                 'Q': 'Q no data',
                 'X': 'I+Q'
             }
            },
        '7': {'band': 'E5b', 'frequency': 1207.140,
             'channel_ids': {
                 'I': 'I F/NAV OS/CS/SoL',
                 'Q': 'Q no data',
                 'X': 'I+Q'
             }
            },
        '8': {'band': 'E5', 'frequency': 1191.795,
             'channel_ids': {
                 'I': 'I',
                 'Q': 'Q',
                 'X': 'I+Q'
             }
            },
        '6': {'band': 'E6', 'frequency': 1278.75,
             'channel_ids': {
                 'A': 'A PRS',
                 'B': 'B C/NAV CS',
                 'C': 'C no data',
                 'X': 'B+C',
                 'Z': 'A+B+C'
             }
            },
    },
    'BDS':{
        '2': {'band':'B1', 'frequency':1561.098,
                'channel_ids':{
                'I': 'I',
                'Q': 'Q',
                'X': 'I+Q'
               }
              },
        '7': {'band':'B2', 'frequency':1207.14,
               'channel_ids':{
                 'I': 'I',
                 'Q': 'Q',
                 'X': 'I+Q'
               }
              },
        '6': {'band':'B3', 'frequency': 1268.52,
                'channel_ids':{
                 'I': 'I',
                 'Q': 'Q',
                 'X': 'I+Q'
                }
            },
        # redundancy to support older RINEX 3.02 versions:
        '1': {'band':'B1', 'frequency': 1561.098,
                'channel_ids':{
                'I': 'I',
                'Q': 'Q',
                'X': 'I+Q'
               }
              },
    },
    'SBAS': {
        '1': {'band': 'L1', 'frequency': 1575.42,
             'channel_ids': {
                 'C': 'C/A',
             }
            },
        '5': {'band': 'L5', 'frequency': 1176.45,
             'channel_ids': {
                 'I': 'I',
                 'Q': 'Q',
                 'X': 'I+Q'
             }
            },
    },
    'QZSS': {
        '1': {'band': 'L1', 'frequency': 1575.42,
             'channel_ids': {
                 'C': 'C/A',
                 'S': 'L1C (D)',
                 'L': 'L1C (P)',
                 'X': 'L1C (D+P)',
                 'Z': 'L1-SAIF',
             }
            },
        '2': {'band': 'L2', 'frequency': 1227.60,
             'channel_ids': {
                 'S': 'L2C (M)',
                 'L': 'L2C (L)',
                 'X': 'L2C (M+L)',
             }
            },
        '5': {'band': 'L5', 'frequency': 1176.45,
             'channel_ids': {
                 'I': 'I',
                 'Q': 'Q',
                 'X': 'I+Q',
             }
            },
        '6': {'band': 'LEX', 'frequency': 1278.75,
             'channel_ids': {
                 'S': 'S',
                 'L': 'L',
                 'X': 'S+L',
             }
            },
    },
    'IRNSS': {
        '5': {'band': 'L5', 'frequency': 1176.45,
             'channel_ids': {
                 'A': 'A SPS',
                 'B': 'B RS (D)',
                 'C': 'C RS (P)',
                 'X': 'B+C',
             }
            },
        '9': {'band': 'S', 'frequency': 2492.028,
             'channel_ids': {
                 'A': 'A SPS',
                 'B': 'B RS (D)',
                 'C': 'C RS (P)',
             }
            },
    }
}

PREFERRED_BAND_TRIPLETS = {
    'GPS': ('L1', 'L2', 'L5'),
    'GLONASS': ('G1', 'G2', 'G3'),
    #'Galileo': ('E1', 'E5', 'E6'),
    'Galileo': ('E1', 'E5a', 'E5b'),
    'BDS': ('B1', 'B2', 'B3'),
    'SBAS': None,
    'QZSS': ('L1', 'L2', 'L5'),
    'IRNSS': None
}

CHANNEL_PREFERENCES = {
    'GPS': {
        'L1': ['X', 'L', 'S', 'C', 'P', 'W', 'Y', 'M', 'N'],
        'L2': ['X', 'L', 'S', 'C', 'Y', 'M', 'D', 'W', 'N'],
        'L5': ['X', 'Q', 'I']
    },
    'GLONASS': {
        'G1': ['C', 'P'],
        'G2': ['C', 'P'],
        'G3': ['X', 'Q', 'I']
    },
    'Galileo': {
        'E1': ['X', 'Z', 'A', 'B', 'C'],
        'E5a': ['X', 'Q', 'I'],
        'E5b': ['X', 'Q', 'I'],
        'E5': ['X', 'Q', 'I'],
        'E6': ['X', 'Z', 'A', 'B', 'C'],
    },
    'BDS': {
        'B1': ['X', 'Q', 'I'],
        'B2': ['X', 'Q', 'I'],
        'B3': ['X', 'Q', 'I'],
    },
    'SBAS': {
        'L1': ['C'],
        'L5': ['X', 'Q', 'I']
    },
    'QZSS': {
        'L1': ['X', 'L', 'S', 'C', 'Z'],
        'L2': ['X', 'L', 'S'],
        'L5': ['X', 'Q', 'I'],
        'LEX': ['X', 'L', 'S']
    },
    'IRNSS': {
        'L5': ['X', 'A', 'B', 'C'],
        'S': ['A', 'B', 'C']
    }
}

def parse_value(val_str, dtype=float, err_val=nan):
    val_str = val_str.strip()
    if val_str == '':
        return err_val
    try:
        return dtype(val_str)
    except Exception:
        return err_val

def parse_RINEX3_header(lines):
    '''
    ------------------------------------------------------------
    Given list of lines corresponding to the header of a RINEX 3
    file, parses the header of the file and returns a dictionary
    containing the header information.
    
    Input
    -----
    `lines` -- lines corresponding to RINEX header
    
    Output
    ------
    dictionary containing RINEX header information
    '''
    header = {}
    header['system_obs_types'] = {}
    header['comments'] = []
    lines = iter(lines)
    try:
        while True:
            line = next(lines)
            header_label = line[60:].strip()
            if header_label == 'COMMENT':
                header['comments'].append(line[0:60])
            elif header_label == 'RINEX VERSION / TYPE':
                header['format_version'] = line[0:20].strip()
                header['observation_type'] = line[20:40].strip()
                header['sat_systems'] = line[40:60].strip()
            elif header_label == 'PGM / RUN BY / DATE':
                header['file_creation_program'] = line[0:20].strip()
                header['file_creation_agency'] = line[20:40].strip()
                header['file_creation_epoch'] = line[40:55].strip()
            elif header_label == 'MARKER NAME':
                header['marker_name'] = line[0:60].strip()
            elif header_label == 'MARKER NUMBER':
                header['marker_number'] = line[0:60].strip()
            elif header_label == 'OBSERVER / AGENCY':
                header['observer'] = line[0:20].strip()
                header['agency'] = line[20:60].strip()
            elif header_label == 'REC # / TYPE / VERS':
                header['receiver_number'] = line[0:20].strip()
                header['receiver_type'] = line[20:40].strip()
                header['receiver_version'] = line[40:60].strip()
            elif header_label == 'ANT # / TYPE':
                header['antenna_number'] = line[0:20].strip()
                header['antenna_type'] = line[20:40].strip()
            elif header_label == 'APPROX POSITION XYZ':
                header['approx_position_xyz'] = \
                    (parse_value(line[0:14]), parse_value(line[14:28]), parse_value(line[28:42]))
            elif header_label == 'SYS / # / OBS TYPES':
                system_letter = line[0:3].strip()
                number_of_obs = parse_value(line[3:6], int)
                obs = line[6:60].split()
                if system_letter not in header['system_obs_types'].keys():
                    header['system_obs_types'][system_letter] = []
                header['system_obs_types'][system_letter] += obs
                number_of_obs -= len(obs)
                # Use continuation line(s) for more than 13 observation descriptors
                while number_of_obs > 0:
                    line = next(lines)
                    assert(line[60:].strip() == 'SYS / # / OBS TYPES')
                    obs = line[6:60].split()
                    header['system_obs_types'][system_letter] += obs
                    number_of_obs -= len(obs)
            elif header_label == 'SIGNAL STRENGTH UNIT':
                header['signal_strength_unit'] = line[0:60].strip()
            elif header_label == 'INTERVAL':
                header['interval'] = parse_value(line[0:60].strip())
            elif header_label == 'TIME OF FIRST OBS':
                header['time_of_first_obs'] = line[0:60].strip()
            elif header_label == 'TIME OF LAST OBS':
                header['time_of_last_obs'] = line[0:60].strip()
            elif header_label == 'RCV CLOCK OFFS APPL':
                header['rcv_clock_offs_appl'] = line[0:60].strip()
            elif header_label == 'SYS / PHASE SHIFT':
                if not hasattr(header, 'phase_shifts'):
                    header['phase_shifts'] = {}
                system_letter = line[0:1]
                if system_letter not in header['phase_shifts'].keys():
                    header['phase_shifts'][system_letter] = {}
                signal_id = line[2:5]
                shift = parse_value(line[6:15])
                header['phase_shifts'][system_letter][signal_id] = shift
            elif header_label == 'GLONASS SLOT / FRQ #':
                num_sats = parse_value(line[0:4], int)
                header['frequency_numbers'] = {}
                while num_sats > 0:
                    sat_ids_and_slots = line[4:60].split()
                    for i in range(len(sat_ids_and_slots) // 2):
                        sat_id, val_str = sat_ids_and_slots[2 * i], sat_ids_and_slots[2 * i + 1]
                        header['frequency_numbers'][sat_id] = parse_value(val_str, int)
                    num_sats -= len(sat_ids_and_slots) // 2
                    line = next(lines)
            elif header_label == 'LEAP_SECONDS':
                pass
    except StopIteration:
        pass
    return header

def parse_RINEX3_obs_data(lines, system_obs_types):
    '''
    ------------------------------------------------------------
    Given `lines` corresponding to the RINEX observation file
    data (non-header) lines, and a list of the types of
    observations recorded at each epoch, produces a dictionary
    containing the observation time and values for each
    satellite.
    
    Input
    -----
    `lines` -- data lines from RINEX observation file
    `system_obs_types` -- list of the observations reported at
        each epoch
    
    Output
    ------
    `data` -- dictionary of format:
        {<sat_id>: {'index': [<int...>], <obs_id>: [<values...>]}}
    `time` -- list of times (datetime64) corresponding to epochs
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
            year = parse_value(line[2:6], int)
            month = parse_value(line[7:9], int)
            day = parse_value(line[10:12], int)
            hour = parse_value(line[13:15], int)
            minute = parse_value(line[16:18], int)
            seconds = parse_value(line[19:29])
            if isnan(seconds):
                microseconds = nan
            else:
                microseconds = int(1e6 * (seconds % 1))
                seconds = int(seconds)
            dt = datetime64(datetime(year, month, day, hour, minute, seconds, microseconds))
            time.append(dt)
            flag = parse_value(line[30:32], int)
            num_sats = parse_value(line[32:35], int)
            # exception could happen here is `num_sats` parses to NaN -- need robust control over raising exception here.
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
                        obs_val = parse_value(obs_str)
                    data[sat_id][obs_type].append(obs_val)
                data[sat_id]['index'].append(epoch_index)
            epoch_index += 1
    except StopIteration:
        pass
    return data, time

def transform_values_from_RINEX3_obs(data, frequency_numbers=None):
    '''
    ------------------------------------------------------------
    Transforms output from `parse_RINEX3_obs_data` to more
    useful format.
    
    Input:
    -------
    `rinex_data` -- Python dictionary with format:
        {
            <sat_id>: {
                    'index': [<int>,...],
                    <obs_id>: [<values...>]
                }
        }
    `frequency_numbers` -- GLONASS frequency numbers obtained
        from RINEX header
        
    Output:
    -------
    `data` -- dictionary in format:
        {<sat_id>: {
                'index': ndarray,
                <sig_id>: {
                    <channel_id>: {
                        <obs_name>: ndarray
                    }
                }
            }
        }
        
    Note: the third character of RINEX observation ID is
    used as `channel_id`
    '''
    new_data = {}
    for sat_id in data.keys():
        new_data[sat_id] = {}
        system_letter = sat_id[0]
        constellation = CONSTELLATION_LETTERS[system_letter]
        mapping = BAND_AND_CHANNEL_MAPPINGS[constellation]
        for obs_id in data[sat_id].keys():
            if obs_id == 'index':
                new_data[sat_id]['index'] = array(data[sat_id]['index'], dtype=int)
                continue
            val_arr = array(data[sat_id][obs_id])
            if numpy.all(numpy.isnan(val_arr)):
                continue
            obs_letter, obs_band, obs_channel = obs_id
            band = mapping[obs_band]['band']
            frequency = mapping[obs_band]['frequency']  # originally in MHz
            if constellation == 'GLONASS' and callable(frequency):
                if frequency_numbers is not None and sat_id in frequency_numbers.keys():
                    frequency = frequency(frequency_numbers[sat_id])
                else:
                    frequency = nan
            channel_desc = mapping[obs_band]['channel_ids'][obs_channel]
            obs_name = OBSERVATION_LETTERS[obs_letter]
            if band not in new_data[sat_id].keys():
                new_data[sat_id][band] = {'frequency': frequency * 1e6}
            if obs_channel not in new_data[sat_id][band].keys():
                new_data[sat_id][band][obs_channel] = {'channel_desc': channel_desc}
            new_data[sat_id][band][obs_channel][obs_name] = array(data[sat_id][obs_id])
    return new_data

def parse_RINEX3_obs_file(filepath):
    '''
    ------------------------------------------------------------
    Given the filepath to a RINEX observation file, parses and
    returns header and observation data.
    
    Input
    -----
    `filepath` -- filepath to RINEX observation file

    Output
    ------
    `header, observations` where `header` is a dictionary
    containing the parsed header information and `observations`
    is a dictionary containing the observation data in the
    format:
        
        {
            'time': ndarray,
            'satellites': {
                <sat_id>: {
                    'index': ndarray,
                    <obs_id>: ndarray
                }
            }
        }
        
    Note: `time` in `observations` is in GPST seconds
    '''
    with open(filepath, 'r') as f:
        lines = list(f.readlines())
    if len(lines) == 0:
        raise Exception('Error when parsing RINEX 3 file.  The file appears to be empty.')
    for i, line in enumerate(lines):
        if line.find('END OF HEADER') >= 0:
            break
    header_lines = lines[:i + 1]
    obs_lines = lines[i + 1:]
    header = parse_RINEX3_header(header_lines)
    if 'system_obs_types' not in header.keys():
        raise Exception('RINEX header must contain `SYS / # / OBS TYPES` and `header` dict from `parse_RINEX3_header` must contain corresponding dictionary `system_obs_types`')
    obs_data, time = parse_RINEX3_obs_data(obs_lines, header['system_obs_types'])
    if 'frequency_numbers' in header.keys():
        obs_data = transform_values_from_RINEX3_obs(obs_data, header['frequency_numbers'])
    else:
        obs_data = transform_values_from_RINEX3_obs(obs_data)
    gps_epoch = datetime64(datetime(1980, 1, 6))
    time = (array(time) - gps_epoch).astype(float) / 1e6  # dt64 is in microseconds
    observations = {'time': time, 'satellites': obs_data}
    return header, observations

