from config import *

from solpy import enphase as e

import pandas as pd
import numpy as np

e.APIKEY = config.get('enphase','key')

def getData(daterange):
    '''Get Enphase data for the given date range
    data is returned as a pd.DataFrame'''

    userid = config.get('enphase','userid')

    system_ids = config.get('enphase','systems').split()
    timezone = config.get('global','timezone')

    systems = [ e.System(sid, userid) for sid in system_ids]

    df = pd.DataFrame()
    for system in systems:
        s = pd.Series([],index=[])
        for d in daterange:
            begin = d.value//10**9
            end   = d.replace(hour=23,minute=59,second=59).value//10**9
            intervals = system.stats(begin,end)['intervals']
            dates = [d['end_at'] for d in intervals]
            data  = [d['powr']   for d in intervals]

            data = np.array(data,dtype=float)
            data /= 12000
            dates = np.array(dates,dtype=int)
            dates -= 300
            dates = dates.astype('datetime64[s]')
            s = s.append(pd.Series(data,index=dates))
        df.loc[:,system.system_id] = s.tz_localize('UTC').tz_convert(timezone)
    return df

