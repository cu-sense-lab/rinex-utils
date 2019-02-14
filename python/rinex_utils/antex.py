from types import SimpleNamespace
from datetime import datetime, timezone, timedelta
from time_utils.leap_seconds import utc_tai_offset
from time_utils.gpst import GPS_TAI_OFFSET


def parse_igs_antex(filepath):
    '''
    See: http://www.igs.org/assets/txt/antex14.txt
    '''
    def set_attributes(ns, attrs, vals):
        for (attr, val) in zip(attrs, vals):
            setattr(ns, attr, val)
    def get_utc_time(year, month, day, hour, minute, second, microsecond):
        '''Given GPS time in year/month/day/hour/minute/seconds format, return UTC datetime'''
        dt = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
        return dt - (utc_tai_offset(dt) - GPS_TAI_OFFSET)
    antennas = []
    with open(filepath, 'r') as f:
        lines = iter(f.readlines())
        line = next(lines)
        while line != None:
            label = line[60:].strip()
            if label == 'COMMENT':
                pass
            elif label == 'ANTEX VERSION / SYST':
                pass
            elif label == 'PCV TYPE / REFANT':
                pass
            elif label == 'COMMENT':
                pass
            elif label == 'END OF HEADER':
                pass
            elif label == 'START OF ANTENNA':
                antenna = SimpleNamespace(frequencies={})
                antennas.append(antenna)
            elif label == 'TYPE / SERIAL NO':
                antenna.antenna_type = line[0:20].strip()
                cospar_id = line[50:60].strip()  # use as proxy to determine if sat or receiver
                if cospar_id == '':
                    antenna.serial_no = line[20:40].strip()
                else:
                    antenna.satellite_code_1 = line[20:40].strip()
                    antenna.satellite_code_2 = line[40:50].strip()
                    antenna.cospar_id = cospar_id
            elif label == 'METH / BY / # / DATE':
                antenna.calibration_method = line[0:20].strip()
                antenna.agency_name = line[20:40].strip()
                antenna.num_calibrated = int(line[40:46].strip())
                antenna.date = line[50:60].strip()
            elif label == 'DAZI':
                antenna.azimuth_incr = float(line[0:60].strip())
            elif label == 'ZEN1 / ZEN2 / DZEN':
                antenna.zen1 = float(line[4:9].strip())
                antenna.zen2 = float(line[10:15].strip())
                antenna.dzen = float(line[16:21].strip())
            elif label == '# OF FREQUENCIES':
                antenna.n_freqs = int(line[0:60])
            elif label == 'VALID FROM':
                year = int(line[0:6])
                month = int(line[6:12])
                day = int(line[12:18])
                hour = int(line[18:24])
                minute = int(line[24:30])
                seconds = float(line[30:42])
                second, microsecond = int(seconds), int(1e6 * (seconds % 1))
                antenna.valid_start = get_utc_time(year, month, day, hour, minute, second, microsecond)
            elif label == 'VALID UNTIL':
                year = int(line[0:6])
                month = int(line[6:12])
                day = int(line[12:18])
                hour = int(line[18:24])
                minute = int(line[24:30])
                seconds = float(line[30:42])
                second, microsecond = int(seconds), int(1e6 * (seconds % 1))
                antenna.valid_end = get_utc_time(year, month, day, hour, minute, second, microsecond)
            elif label == 'SINEX CODE':
                antenna.sinex_code = line[0:10].strip()
            elif label == 'START OF FREQUENCY':
                freq_code = line[0:10].strip()
                frequency = SimpleNamespace(code=freq_code)
                antenna.frequencies[freq_code] = frequency
            elif label == 'NORTH / EAST / UP':
                frequency.north = float(line[3:12])
                frequency.east = float(line[12:21])
                frequency.up = float(line[21:30])
                line = next(lines)  # next line is always DAZI followed by values
                frequency.dazi = [float(x) for x in line[9:].strip().split()]
            elif label == 'END OF FREQUENCY':
                freq_code = line[0:10].strip()
                assert(frequency.code == freq_code)
            elif label == 'START OF FREQ RMS':
                pass
            elif label == 'END OF FREQ RMS':
                pass
            line = next(lines, None)
    return antennas


