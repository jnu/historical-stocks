'''
yahoo-finance/symbol.py
'''

import urllib
import urllib2
import datetime
import json
import csv
from collections import OrderedDict


# Utils

def _url_month_formatter(m):
    return '%02d' % (m - 1)

def _process_keys(a):
    return [s.lower().replace(' ', '_') for s in a]

def _default_json(obj):
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()

def _get_type(o):
    t = type(o)
    return o if t is type else t


# Helper classes

class Record(object):

    def __init__(self, **kwargs):
        # Copy fields onto instance
        for k, parse in self.fields.items():
            if k in kwargs:
                setattr(self, k, parse(kwargs[k]))

        # Determine which keys have not been assigned
        unassigned = set(self.fields.keys()) - set(kwargs.keys())

        # Call any implementation methods that derive unassigned keys
        for key in unassigned:
            if hasattr(self, key):
                f = getattr(self, key)
                if callable(f):
                    setattr(self, key, f())

    def __repr__(self):
        return json.dumps(self.__dict__, default=_default_json)

    def __iter__(self):
        for k in type(self).fields:
            yield getattr(self, k)

    @classmethod
    def header(cls):
        return cls.fields.keys()

    @staticmethod
    def value(record):
        T = type(record)
        # Use fields from class, not the instance, in case they're overridden
        return [getattr(record, k, None) for k in T.fields.keys()]


class HistoricalStockRecord(Record):

    fields = OrderedDict([
        ('key', str),
        ('symbol', str),
        ('volume', int),
        ('adj_close', float),
        ('high', float),
        ('low', float),
        ('date', lambda s: datetime.datetime(*[int(n) for n in s.split('-')])),
        ('close', float),
        ('open', float)
    ])

    def key(self):
        return '%s|%s' % (self.date, self.symbol)


# Main class

def check_status(func):
    def safe_invoke(self, *args, **kwargs):
        self._Symbol__raise()
        # Proceed with calling the function
        return func(self, *args, **kwargs)
    return safe_invoke

class Symbol(object):

    # status flags
    OK = 0x00
    UNKNOWN_SYMBOL = 0x01
    UNKNOWN_ERROR = 0x02

    exceptions = {
        OK: None,
        UNKNOWN_SYMBOL: 'Unknown Symbol',
        UNKNOWN_ERROR: 'Unknown Error'
    }

    history_root = 'http://real-chart.finance.yahoo.com/table.csv'

    def __init__(self, sym):
        self.__sym = sym.upper()
        self.status = self.OK

    def __raise(self):
        # Get the exception if there is one
        msg = self.exceptions[self.status]
        if msg:
            raise Exception(msg)

    @check_status
    def get_historical(self, start=None, end=None):
        if start is None:
            start = datetime.datetime(1900, 1, 1)

        if end is None:
            end = datetime.datetime.today()

        symbol = self.__sym

        query_params = {
            's': symbol,
            'a': _url_month_formatter(start.month),
            'b': start.day,
            'c': start.year,
            'd': _url_month_formatter(end.month),
            'e': end.day,
            'f': end.year,
            'g': 'd',
            'ignore': '.csv'
        }

        query_str = urllib.urlencode(query_params)

        url = '%s?%s' % (self.history_root, query_str)

        try:
            uh = urllib2.urlopen(url)
        except urllib2.HTTPError as e:
            if e.code == 404:
                self.status = self.UNKNOWN_SYMBOL
            else:
                self.status = self.UNKNOWN_ERROR
            self.__raise()


        records = []

        head = None
        for line in csv.reader(uh):
            if head is None:
                head = _process_keys(line)
                continue
            d = { head[i]: val for i, val in enumerate(line) }
            record = HistoricalStockRecord(symbol=symbol, **d)
            records.append(record)

        return records
