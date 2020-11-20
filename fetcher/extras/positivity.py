from datetime import datetime
import os
import re

import pandas as pd
from fetcher.extras.common import zipContextManager


def handle_dc(res, mapping):
    ppr = res[0]

    ppr = ppr.filter(mapping.keys()).rename(columns=mapping)
    ppr['UNITS'] = 'Tests'
    ppr['WINDOW'] = 'Week'
    return ppr.to_dict(orient='records')


def handle_ga(res, mapping):
    tagged = []
    filename = "pcr_positives.csv"
    with zipContextManager(res[-1]) as zipdir:
        df = pd.read_csv(open(os.path.join(zipdir, filename), 'r'),
                         parse_dates=['report_date'])
        df = df[df['county'] == 'Georgia']

        # alltime/daily
        latest = df.sort_values('report_date').iloc[-1]
        # daily
        tagged.append({
            'TOTAL': latest['ALL PCR tests performed'],
            'POSITIVE': latest['All PCR positive tests'],
            'TIMESTAMP': latest['report_date'],
            'WINDOW': 'Day',
            'UNITS': 'Tests'
        })
        # all time
        tagged.append({
            'TOTAL': latest['Running total of all PCR tests'],
            'POSITIVE': latest['Running total of all PCR tests.1'],
            'TIMESTAMP': latest['report_date'],
            'WINDOW': 'Alltime',
            'UNITS': 'Tests'
        })

        # separate it to 7 & 14 rates
        windows = {'Week': '7 day percent positive',
                   '14Days': '14 day percent positive'}
        for window, column in windows.items():
            pct = df.filter(mapping.keys()).rename(columns=mapping).drop(columns='PPR')
            pct['PPR'] = pd.to_numeric(df[column], errors='coerce')
            pct['WINDOW'] = window
            pct['UNITS'] = 'Tests'
            tagged.append(pct.to_dict(orient='records'))

    return tagged


def handle_ky(res, mapping):
    tagged = {}

    # soup time
    soup = res[-1]
    title = soup.find('span', string=re.compile("Positivity Rate"))
    number = title.find_next_sibling()
    tagged['PPR'] = float(number.get_text(strip=True).replace('%', ''))
    tagged['TIMESTAMP'] = datetime.now().timestamp()

    return tagged


def handle_wi(res, mapping):
    # 0 - by tests
    # 1 - by people

    mapped = []
    units = ['Tests', 'People']

    # TODO: example of cheating:
    # could be better to send constants from the query def here

    for i, df in enumerate(res):
        df.index.name = 'Date'
        df['Date'] = df.index
        df = df.filter(mapping.keys())
        df = df.groupby(level=0).last().rename(columns=mapping)
        df['UNITS'] = units[i]
        df['WINDOW'] = 'Week'
        mapped.append(df.to_dict(orient='records'))

    return mapped
