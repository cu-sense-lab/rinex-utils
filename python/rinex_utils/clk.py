from rinex_utils.rinex3 import parse_RINEX3_header, parse_value
from types import SimpleNamespace
from datetime import datetime
from numpy import isnan

def parse_RINEX3_clk_file(filepath, designators='all'):
    '''
    ------------------------------------------------------------
    Given the filepath to a RINEX clock file, parses and
    returns header and clock data.
    
    Input
    -----
    `filepath` -- filepath to RINEX clock file
    `designators` -- list of designators for the objects whose
        clock data should be parsed and stored.  Can be IGS
        4-character station designator or the 3-character
        satellite ID.  If designators is `'all'` (default),
        parses all information in file.

    Output
    ------
    `header, clock_obs` where `header` is a dictionary
    containing the parsed header information and `clock_obs`
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
    clk_lines = lines[i + 1:]
    header = parse_RINEX3_header(header_lines)
    clk_data = parse_RINEX3_clk_data(clk_lines, designators)
    return header, clk_data

def parse_RINEX3_clk_data(lines, designators):
    '''
    See: ftp://igs.org/pub/data/format/rinex_clock300.txt
    '''
    data = {}
    lines = iter(lines)
    try:
        line = next(lines)
        while True:
            clock_data_type = line[:2]
            designator = line[3:7].strip()
            if designators is not 'all' and designator not in designators:
                line = next(lines)
                continue
            if designator not in data.keys():
                data[designator] = SimpleNamespace(epochs=[], values=[])
            epoch = line[8:36].strip()
            year = parse_value(epoch[0:4], int)
            month = parse_value(epoch[5:7], int)
            day = parse_value(epoch[8:10], int)
            hour = parse_value(epoch[11:13], int)
            minute = parse_value(epoch[14:16], int)
            seconds = parse_value(epoch[17:27])
            if isnan(seconds):
                microseconds = nan
            else:
                microseconds = int(1e6 * (seconds % 1))
                seconds = int(seconds)
            dt = datetime(year, month, day, hour, minute, seconds, microseconds)
#             print(year, month, day, hour, minute, seconds)
            n_values = parse_value(line[36:40], int)
            line = line[40:].rjust(40)         
            if not isnan(n_values) and n_values > 2:
                line += next(lines).rjust(80)
            values = []
            for i in range(n_values):
                values.append(parse_value(line[i * 20:(i + 1) * 20]))
            data[designator].epochs.append(dt)
            data[designator].values.append(values)
            line = next(lines)
    except StopIteration:
        pass
    return data

