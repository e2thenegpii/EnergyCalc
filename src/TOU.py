from enum import Enum

from datetime import datetime, date
from dateutil.relativedelta import relativedelta, MO
import argparse
import holidays
import pandas as pd

class BGEHolidays(holidays.HolidayBase):
    def _populate(self, year):
        holidays.UnitedStates._populate(self, year)

        # Remove Martin Luther King Day
        self.pop(date(year, 1, 1) + relativedelta(weekday=MO(+3)), None)

        # Remove Columbus Day
        self.pop(date(year, 10, 1) + relativedelta(weekday=MO(+2)), None)

        # Remove Veterans Day
        self.pop(date(year, 11, 11), None)

        # Add good friday
        self[holidays.easter(year) + relativedelta(days=-2)] = 'Good Friday'

class TimeOfUse(Enum):
    peak = 0
    shoulder = 1
    offpeak = 2

class Season(Enum):
    Winter = 0
    Summer = 1

    @classmethod
    def get(cls, dt):
        d = dt.date()
        if date(dt.year, 6, 1) <= d and date(dt.year, 9, 30) >= d:
            return cls.Summer
        return cls.Winter

class Schedule(Enum):
    R = 'R'
    RL = 'RL'
    EV = 'EV'
    EVP = 'EVP'

    def getTOU(self, dt):
        d = dt.date()
        t = dt.time()
        bge_holidays = BGEHolidays(dt.year)

        if self == self.R:
            return TimeOfUse.offpeak
        elif self == self.RL:
            if Season.get(dt) == Season.Summer:
                if (t.hour >=10 and t.hour < 20) and \
                    (dt.weekday() < 5) and \
                    (d not in bge_holidays):
                    return TimeOfUse.peak
                elif ((t.hour >= 7 and t.hour < 10) or (t.hour >= 20 and t.hour < 23)) and \
                    (dt.weekday() < 5) and \
                    (d not in bge_holidays):
                    return TimeOfUse.shoulder
                else:
                    return TimeOfUse.offpeak
            else:
                if ((t.hour >= 7 and t.hour < 11) or (t.hour >= 17 and t.hour < 21)) and \
                    (dt.weekday() < 5) and \
                    (d not in bge_holidays):
                    return TimeOfUse.peak
                elif (t.hour >= 11 and t.hour < 17) and \
                    (dt.weekday() < 5) and \
                    (d not in bge_holidays):
                    return TimeOfUse.shoulder
                else:
                    return TimeOfUse.offpeak

        elif self in (self.EV, self.EVP):
            if Season.get(dt) == Season.Summer:
                if (t.hour >= 10 and t.hour < 20) and \
                    (dt.weekday() < 5) and \
                    (d not in bge_holidays):
                    return TimeOfUse.peak
                else:
                    return TimeOfUse.offpeak
            else:
                if ((t.hour >= 7 and t.hour < 11) or (t.hour >= 17 and t.hour < 21)) and \
                    (dt.weekday() < 5) and \
                    (d not in bge_holidays):
                    return TimeOfUse.peak
                else:
                    return TimeOfUse.offpeak

rates = {
    (Schedule.R, Season.Summer, TimeOfUse.offpeak): .06722,
    (Schedule.R, Season.Winter, TimeOfUse.offpeak): .07805,
    (Schedule.RL, Season.Summer, TimeOfUse.peak): .08465,
    (Schedule.RL, Season.Summer, TimeOfUse.shoulder): .06069,
    (Schedule.RL, Season.Summer, TimeOfUse.offpeak): .05744,
    (Schedule.RL, Season.Winter, TimeOfUse.peak): .09053,
    (Schedule.RL, Season.Winter, TimeOfUse.shoulder): .07944,
    (Schedule.RL, Season.Winter, TimeOfUse.offpeak): .07166,
    (Schedule.EV, Season.Summer, TimeOfUse.peak): .1227,
    (Schedule.EV, Season.Summer, TimeOfUse.offpeak): .03886,
    (Schedule.EV, Season.Winter, TimeOfUse.peak): .18474,
    (Schedule.EV, Season.Winter, TimeOfUse.offpeak): .0426,
    (Schedule.EVP, Season.Summer, TimeOfUse.peak): .03886,
    (Schedule.EVP, Season.Summer, TimeOfUse.offpeak): .03886,
    (Schedule.EVP, Season.Winter, TimeOfUse.peak): .0426,
    (Schedule.EVP, Season.Winter, TimeOfUse.offpeak): .0426
}

def get_rate(dt, schedule = Schedule.R):
    bge_holidays = BGEHolidays(dt.year)

    season = Season.get(dt)
    tou = schedule.getTOU(dt)

    return rates[(schedule, season, tou)]

def process_row(x):
    dt = x['DATE_START TIME']
    val = x['USAGE']
    return pd.Series([dt] + [get_rate(dt, x) * (val + .0700) for x in Schedule], index=['DATE_START TIME'] + [x.value for x in Schedule])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', type=argparse.FileType('r'))

    args = parser.parse_args()

    df = pd.read_csv(args.input_file, parse_dates=[['DATE', 'START TIME']])[['DATE_START TIME', 'USAGE']]

    schedules = df.apply(process_row, axis=1)
    print(schedules[['R', 'RL', 'EV', 'EVP']].sum())

if __name__ == '__main__':
    main()
