import re
from types import SimpleNamespace
from datetime import datetime, timezone

def parse_rinex_nav(filepath, century=2000):
    '''
    Given filepath to RINEX Navigation file, parses navigation into ephemeris.
    Returns dictionary {prn: [SimpleNamespace]} of ephemeris objects
    
    # (2016/05/30) function requiring ephemeris paramters need the following names:
    # e - eccentricity
    # t_oe - time of ephemeris
    # i_0 - inclination at reference time (rad)
    # a - semi-major axis (m); usually given as SQRT
    # omega_dot - rate of right ascension (rad/s)
    # omega_0 - right ascension at week (rad)
    # omega - argument of perigee
    # M_0 - mean anomaly of reference time (rad)
    # week - GPS week number
    # delta_n - mean motion difference (rad/s)
    # i_dot - rate of inclination angle (rad/s)
    # c_us - argument of latitude (amplitude of cosine, radians)
    # c_rs - orbit radius (amplitude of sine, meters)
    # c_is - inclination (amplitude of sine, meters)
    # c_uc - argument of latitude (amplitude of cosine, radians)
    # c_rc - orbit radius (amplitude of cosine, meters)
    # c_ic - inclination (amplitude of cosine, meters)century = 2000
    '''
    epoch_pattern = '(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+)\s(\s?\d+\.\d)'
    number_pattern = '\n?\s*([+-]?\d+\.\d{12}D[+-]?\d{2})'
    pattern = epoch_pattern + 29 * number_pattern
    data = {}
    with open(filepath, 'r') as f:
        matches = re.findall(pattern, f.read())
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
            epoch = datetime(year, month, day, hour, minute, int(second), int(1e6 * (second % 1)), tzinfo=timezone.utc)
            eph = SimpleNamespace(
                epoch=epoch,
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
