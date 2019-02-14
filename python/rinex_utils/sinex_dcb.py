from datetime import datetime, timedelta, timezone
from .dcb import create_mgex_dcb_dict


def parse_sinex_date_str(dt_str):
    '''Parse string with format `{yyyy}:{yday}:{seconds}`
    where seconds is seconds into the day.
    '''
    year, yday, sec = dt_str.split(':')
    return datetime(int(year), 1, 1, tzinfo=timezone.utc) \
        + timedelta(days=int(yday) - 1) + timedelta(seconds=int(sec))


SINEX_TYPES = {
    'BIAS/SOLUTION': {
        'BIAS': str,
        'SVN': str, 
        'PRN': str, 
        'STATION': str, 
        'OBS1': str, 
        'OBS2': str, 
        'BIAS START': parse_sinex_date_str, 'BIAS END': parse_sinex_date_str,
        'UNIT': str,
        'ESTIMATED VALUE': float,
        'STD DEV': float
    }
}


def parse_sinex_section(lines):
    assert(lines[0].startswith('+'))
    section_name = lines[0][1:].strip()
    if lines[1].startswith('*'):
        # is probably the section header column
        column_names = lines[1][1:].split(' ')
        column_indices = {}
        i0 = 1 
        data = {}
        for name in column_names:
            column_indices[name] = (i0, i0 + len(name))
            data[name] = []
            i0 += len(name) + 1 
        for line in lines[2:]:
            if line.startswith('-') and line[1:].strip() == section_name:
                break
            for name in column_names:
                i0, i1 = column_indices[name]
                data[name].append(line[i0:i1].strip())
        N = len(list(data.values())[0])
        assert(all(len(v) == N for v in data.values()))
        for key in data.keys():
            data[key.replace('_', ' ').strip()] = data.pop(key)
        if section_name in SINEX_TYPES.keys():
            for key in data.keys():
                if key in SINEX_TYPES[section_name]:
                    data[key] = [SINEX_TYPES[section_name][key](item) for item in data[key]]
        return data
    return None

def parse_sinex(filepath):
    sections = []
    section = None
    with open(filepath, 'r') as f:
        for line in f.readlines():
            if line.startswith('+'):
                section = {}
                sections.append(section)
                section['name'] = line[1:].strip()
                section['lines'] = []
            if section is not None:
                if line.startswith('-') and line[1:].strip() == section['name']:
                    # reached end of section
                    section = None
                else:
                    section.lines.append(line)
    data = {}
    for section in sections:
        data[section['name']] = parse_sinex_section(section['lines'])
    return data



def filter_sinex_dcb_data_by_date(dcb_data, dt):
    '''
    `dcb_data` -- 'BIAS/SOLUTION' output from `parse_sinex_dcb` function
    `dt` -- desired applicable datetime of DCB
    Returns: filtered version of `dcb_data`
    '''
    data = {key: [] for key in dcb_data.keys()}
    for i in range(len(dcb_data['BIAS START'])):
        if abs((dt - dcb_data['BIAS START'][i]).total_seconds()) < 86400:
            for key in dcb_data.keys():
                data[key].append(dcb_data[key][i])
    return data


def create_dcb_dict_from_sinex(sinex, dt):
    '''
    `sinex` -- SINEX output from `parse_sinex`
    `dt` -- desired applicable datetime of DCB
    First, mimics `parse_mgex_dcb` by converting parsed SINEX.  Then calls
    `create_mgex_dcb_dict`.
    See `create_mgex_dcb_dict` for more information.
    Returns: `SIGNAL_DCBS` -- dict of form {(<sig1>, <sig2>): {<sp3id>: <value>, ... }, ... }
    '''
    dcb_data = sinex['BIAS/SOLUTION']
    dcb_data = filter_sinex_dcb_data_by_date(dcb_data, dt)
    N = len(dcb_data['PRN'])
    dcb_values = {}
    for i in range(N):
        prn, obs1, obs2, value = (dcb_data[key][i] for key in ('PRN', 'OBS1', 'OBS2', 'ESTIMATED VALUE'))
        if prn not in dcb_values.keys():
            dcb_values[prn] = {}
        if obs1 not in dcb_values[prn].keys():
            dcb_values[prn][obs1] = {}
        keys = ['svid', 'prn', 'site', 'obs1', 'obs2', 'start', 'end', 'value', 'stddev']
        values = [dcb_data[key][i] for key in ('SVN', 'PRN', 'STATION', 'OBS1', 'OBS2',
                                'BIAS START', 'BIAS END', 'ESTIMATED VALUE', 'STD DEV')]
        dcb_values[prn][obs1][obs2] = dict(zip(keys, values))
    return create_mgex_dcb_dict(dcb_values)

