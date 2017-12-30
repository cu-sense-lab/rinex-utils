from types import SimpleNamespace
import numpy
from numpy import array, nan, datetime64
from datetime import datetime
import re

def parse_rinex_header(lines):
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
                header.n_obs = int(line[:10])
                header.obs_types = line[10:58].split()
            elif line[60:].strip() == 'COMMENT':
                pass
    except StopIteration:
        pass
    return header


def parse_nav_data(lines, century=2000):
    '''
    Given filepath to RINEX Navigation file, parses navigation into ephemeris.
    Returns dictionary {prn: [SimpleNamespace]} of ephemeris objects
    
    Output
    ------
    Dictionary of format:
        {<prn>: <namespace>}
    Each namespace contains the following parameters:
        epoch - Python `datetime` object that is the epoch corresponding to the
            ephemeris -- this is also the "Time of Clock" (`t_oc`)
        e - eccentricity
        t_oe - time of ephemeris
        i_0 - inclination at reference time (rad)
        a - semi-major axis (m); usually given as SQRT
        omega_dot - rate of right ascension (rad/s)
        omega_0 - right ascension at week (rad)
        omega - argument of perigee
        M_0 - mean anomaly of reference time (rad)
        week - GPS week number
        delta_n - mean motion difference (rad/s)
        i_dot - rate of inclination angle (rad/s)
        c_us - argument of latitude (amplitude of cosine, radians)
        c_rs - orbit radius (amplitude of sine, meters)
        c_is - inclination (amplitude of sine, meters)
        c_uc - argument of latitude (amplitude of cosine, radians)
        c_rc - orbit radius (amplitude of cosine, meters)
        c_ic - inclination (amplitude of cosine, meters)
    '''
    epoch_pattern = '(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+\.\d)'
    number_pattern = '\n?\s*([+-]?\d+\.\d{12}D[+-]?\d{2})'
    pattern = epoch_pattern + 29 * number_pattern
    data = {}
    matches = re.findall(pattern, '\n'.join(lines))
    for m in matches:
        prn, yy, month, day, hour, minute = (int(i) for i in m[:6])
        second, a0, a1, a2, \
            iode1, c_rs, delta_n, m_0, \
            c_uc, e, c_us, sqrt_a, \
            t_oe, c_ic, omega_0, c_is, \
            i_0, c_rc, omega, omega_dot, \
            i_dot, l2_codes, week, l2p_data, \
            accuracy, health, tgd, iodc, \
            transmit_time, fit_interval = (float(s.replace('D', 'E')) for s in m[6:36])
        year = century + yy
        epoch = datetime64(datetime(year, month, day, hour, minute, int(second), int(1e6 * (second % 1))))
        eph = SimpleNamespace(
            epoch=epoch, a0=a0, a1=a1, a2=a2,
            iode1=iode1, c_rs=c_rs, delta_n=delta_n, m_0=m_0,
            c_uc=c_uc, e=e, c_us=c_us, sqrt_a=sqrt_a,
            t_oe=t_oe, c_ic=c_ic, omega_0=omega_0, c_is=c_is,
            i_0=i_0, c_rc=c_rc, omega=omega, omega_dot=omega_dot,  # TODO check if orbit solutions correct omega
            i_dot=i_dot, l2_codes=l2_codes, week=week, l2p_data=l2p_data,
            accuracy=accuracy, health=health, tgd=tgd, iodc=iodc,
            transmit_time=transmit_time, fit_interval=fit_interval
        )
        if prn not in data.keys():
            data[prn] = []
        data[prn].append(eph)
    return data


def parse_obs_data(lines, observations, century=2000, return_time=False):
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
            yy = int(line[:4])
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
            line = line[32:]
            if num_sats > 16:
                line = (line + next(lines).strip()).replace(' ', '')
            line = line.strip()
            # must replace spaces with zeros: e.g. to convert `'G 1'` to `'G01'`
            sat_ids = [line[3*i:3*(i+1)].replace(' ', '0') for i in range(num_sats)]

            for sat_id in sat_ids:
                # create new entry if `sat_id` is new
                if sat_id not in data.keys():
                    data[sat_id] = {'index': [], 'time': []}
                    for obs_id in observations:
                        data[sat_id][obs_id] = []
                # append time/index first, then append obs values
                data[sat_id]['time'].append(dt)
                data[sat_id]['index'].append(epoch_index)
                # each line of observation values contains up to 5 entries
                # each entry is of width 16, starting at index 0
                num_lines_per_sat = 1 + len(observations) // 5
                line = ''
                while num_lines_per_sat > 0:
                    line += next(lines).replace('\n', '')
                    num_lines_per_sat -= 1
                for i, obs_id in enumerate(observations):
                    try:
                        val = float(line[16 * i:16 * (i + 1)])
                    except Exception:
                        val = nan
                    data[sat_id][obs_id].append(val)
            epoch_index += 1
    except StopIteration:
        pass
    if return_time:
        return data, array(time)
    return data

def transform_values_from_rinex_obs(rinex_data):
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
    rinex_obs_datatypes_mapping = {
        'C1': {'signal': 'L1', 'name': 'pr'},
        'L1': {'signal': 'L1', 'name': 'carrier'},
        'D1': {'signal': 'L1', 'name': 'doppler'},
        'S1': {'signal': 'L1', 'name': 'snr'},
        'C2': {'signal': 'L2', 'name': 'pr'},
        'P2': {'signal': 'L2', 'name': 'pr'},
        'L2': {'signal': 'L2', 'name': 'carrier'},
        'D2': {'signal': 'L2', 'name': 'doppler'},
        'S2': {'signal': 'L2', 'name': 'snr'},
    }
    data = {}
    for sat_id, rnx_sat in rinex_data.items():
        if sat_id not in data.keys():
            data[sat_id] = SimpleNamespace(signals={})
        sat = data[sat_id]
        for obs_name, mapping in rinex_obs_datatypes_mapping.items():
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

def parse_rinex_obs_file(filepath, return_time=False):
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
    header = parse_rinex_header(header_lines)
    if not hasattr(header, 'obs_types'):
        raise Exception('RINEX header must contain `# / TYPES OF OBS.` and `header` namespace from `parse_rinex_header` must contain corresponding list `obs_types`')
    obs_data, obs_time = parse_obs_data(obs_lines, header.obs_types, return_time=True)
    obs_data = transform_values_from_rinex_obs(obs_data)
    if return_time:
        return header, obs_data, obs_time
    return header, obs_data

def parse_rinex_nav_file(filepath):
    '''Given the filepath to a RINEX navigation message file, parses and returns header
    and navigation ephemeris data.
    
    Input
    -----
    `filepath` -- filepath to RINEX navigation file
    
    Output
    ------
    `header, nav_data` where `header` is a namespace containing the parsed header information
        and `nav_data` is a dictionary containing the navigation data in the format:
        {<prn>: [<namespace>, ... ]})}
    
    where each namespace corresponds to a different ephemeris set.  See documentation in
    `parse_nav_data` for information on the contents of each namespace.
        
    Note: `epoch` on the satellite namespace is a `datetime` object
    '''
    with open(filepath, 'r') as f:
        lines = list(f.readlines())
    for i, line in enumerate(lines):
        if line.find('END OF HEADER') >= 0:
            break
    header_lines = lines[:i + 1]
    nav_lines = lines[i + 1:]
    header = parse_rinex_header(header_lines)
    nav_data = parse_nav_data(nav_lines)
    return header, nav_data
