
from datetime import datetime, timezone
from time_utils.gpst import GPS_EPOCH
import numpy
from numpy import nan, zeros, argsort, alltrue, concatenate, diff

def parse_sp3_header(header_lines):

    header = {}

    line = header_lines[0]
    header['version'] = line[:2]
    header['position_velocity_flag'] = line[2]
    header['start_time'] = _sp3_strptime(line[3:31])
    header['number_of_epochs'] = int(line[32:39])
    header['data_used'] = line[40:45].strip()
    header['coordinate_sys'] = line[46:51]
    header['orbit_type'] = line[52:55]
    header['agency'] = line[56:60].strip()

    line = header_lines[1]
    header['gps_week'] = int(line[3:7])
    header['seconds_of_week'] = float(line[8:23])
    header['epoch_interval'] = float(line[24:38])
    header['mod_jul_day_start'] = int(line[39:44])
    header['fractional_day'] = float(line[45:60])

    return header

def _sp3_test_nan(x, nan_value=999999.999999, eps=1e-3):
    '''Tests if `x` is NaN according to SP3 spec, i.e. is within `eps` of `nan_value`'''
    return abs(x - nan_value) < eps

def _sp3_strptime(timestr):
    '''
    Takes SP3 file epoch date string format and returns GPS seconds.
    Because datatime only tracks up to microsecond accuracy, we cannot use 
    the last 2 digits in the seconds decimal.  We will throw an error if the
    last two digits are not 0.  Also, the times in SP3 files are given in GPS time, even
    thought the format is YYYY MM DD HH MM SS.  This means that if we subtract
    the GPS epoch using two UTC datetimes, we'll get the correct time in GPS
    seconds (note, datetime is not leap-second aware, which is why this works).
    '''
    if int(timestr[26:]) != 0:
        raise Exception('`datetime` cannot handle sub-microsecond precision, but epoch in file appears to specify this level of precision.')
    time = datetime.strptime(timestr[:26], '%Y %m %d %H %M %S.%f').replace(tzinfo=timezone.utc)
    return (time - GPS_EPOCH).total_seconds()  # GPS time
    
def _sp3_parse_position_and_clock(line):
    '''
    Returns <vehicle id>, <x-coordinate>, <y-coordinate>, <z-coordinate>, <clock>
    x, y, z coordinates are in units of km and clock offset is in units of microseconds
    '''
    veh_id, x, y, z, c = line[1:4], float(line[4:18]), float(line[18:32]), float(line[32:46]), float(line[46:60])
    x = nan if _sp3_test_nan(x) else x * 1e3
    y = nan if _sp3_test_nan(y) else y * 1e3
    z = nan if _sp3_test_nan(z) else z * 1e3  # convert from km to m
    clock = nan if _sp3_test_nan(c) else c
    return veh_id, x, y, z, clock

def _sp3_parse_velocity_and_clock(line):
    '''
    Returns <vehicle id>, <x-velocity>, <y-velocity>, <z-velocity>, <clock-rate-change>
    x, y, z velocities are in units of dm/s and clock rate is in units of s/s
    '''
    return _sp3_parse_position_and_clock(line)
    

    
def parse_sp3_records(record_lines, parse_position=True, parse_velocity=False):

    epochs = []
    records = []
    for line in record_lines:
        if line.startswith('*'):
            epochs.append(_sp3_strptime(line[2:].strip()))
            records.append({})
        elif line.startswith('P') and parse_position:
            veh_id, x, y, z, c = _sp3_parse_position_and_clock(line)
            records[-1][veh_id] = (x, y, z, c)
        elif line.startswith('V') and parse_velocity:
            veh_id, x, y, z, c = _sp3_parse_velocity_and_clock(line)
            records[-1][veh_id] = (x, y, z, c)
    return epochs, records

def parse_sp3_file(filepath):
    lines = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    if not lines:
        raise Exception('File was empty')
    header_lines = lines[:22]  # there should always be 22 header lines
    record_lines = lines[22:]
    header = parse_sp3_header(header_lines)
    epochs, records = parse_sp3_records(record_lines)
    return header, epochs, records

def parse_sp3_to_ndarray(filepath):
    header, epochs, records = parse_sp3_file(filepath)
    vehicles = set()
    for record in records:
        vehicles = vehicles | set(record.keys())
    vehicles = sorted(list(vehicles))
    N = len(epochs)
    assert(len(records) == N)
    data = {veh: nan * zeros((N, 4)) for veh in vehicles}
    for i, record in enumerate(records):
        for veh, vals in record.items():
            data[veh][i, :] = vals
    return epochs, data

def parse_sp3_data(filepaths, sat_ids='all'):
    headers, epochs_list, records_list = [], [], []
    for filepath in filepaths:
        header, epochs, records = parse_sp3_file(filepath)
        headers.append(header)
        epochs_list.append(epochs)
        records_list.append(records)
    vehicles = set()
    for records in records_list:
        for record in records:
            vehicles = vehicles | set(record.keys())
    if sat_ids != 'all':
        sat_ids = set(sat_ids)
        vehicles = vehicles & sat_ids
    vehicles = sorted(list(vehicles))
    N = sum([len(epochs) for epochs in epochs_list])
    assert(sum([len(records) for records in records_list]) == N)
    data = {veh: nan * zeros((N, 4)) for veh in vehicles}
    all_epochs = concatenate(epochs_list)
    assert(len(all_epochs) == N)
    data = {veh: nan * zeros((N, 4)) for veh in vehicles}
    offset = 0
    for records in records_list:
        for i, record in enumerate(records):
            for veh in vehicles:
                if veh not in record.keys():
                    continue
                data[veh][offset + i, :] = record[veh]
        offset += len(records)
    # sort epochs and remove duplicate epochs
    indices = argsort(all_epochs)
    indices = indices[concatenate(([1], diff(all_epochs[indices]) > 0)).astype(bool)]
    all_epochs = all_epochs[indices]
    for veh in vehicles:
        data[veh] = data[veh][indices, :]
    return all_epochs, data


