import re
from datetime import datetime
from numpy import datetime64
from types import SimpleNamespace
from .rinex2 import parse_RINEX2_header

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
    header = parse_RINEX2_header(header_lines)
    nav_data = parse_nav_data(nav_lines)
    return header, nav_data

