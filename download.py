'''
$ download.py [symbols.txt] [-o/--out data/output.csv]

Get the stocks describe by symbols
'''

from yahoofinance.symbol import Symbol, HistoricalStockRecord
from sys import argv, stderr
import argparse
import re
import csv
import os
import errno
from progressbar import Bar, ETA, Percentage, ProgressBar, Widget


class ProgressLabel(Widget):
    "Simple label widget for ProgressBar"

    def update_label(self, label):
        self.label = label

    def update(self, pbar):
        if pbar.currval == 0:
            return 'Pending'
        elif pbar.finished:
            return 'Finished'
        else:
            return '%s (%d of %d)' % (self.label, pbar.currval, pbar.maxval)


def parse_symbol_files(sym_files):
    '''
    Parse symbols from a list of files.

    Returns a set (no duplicates) of symbols. Symbols in input file need to be
    separated by whitespace (any \s will do - newline, tab, space are fine).
    '''
    all_sym = set()
    slicer = re.compile(r'\s+').split

    for fn in sym_files:
        with open(fn) as fh:
            raw = fh.read()
            sym = slicer(raw)
            all_sym |= set(sym)

    return all_sym


def mkdir_p(path):
    path = os.path.dirname(path)
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise


def run(symbol_files, output_file, error_file=stderr):
    symbols = parse_symbol_files(symbol_files)

    mkdir_p(output_file)

    maxval = len(symbols)
    plabel = ProgressLabel()
    widgets = [Percentage(), Bar(), ' ', plabel, ' ', ETA()]
    progress = ProgressBar(widgets=widgets, maxval=maxval).start()

    with open(error_file, 'w+') as feh:
        with open(output_file, 'w+') as fh:
            writer = csv.writer(fh)
            writer.writerow(HistoricalStockRecord.header())

            for i, s in enumerate(symbols):
                plabel.update_label(s)
                progress.update(i)
                sym = Symbol(s)

                try:
                    records = sym.get_historical()
                except:
                    print >>feh, "Failed to download:\t%s" % s
                    continue

                for record in records:
                    writer.writerow(HistoricalStockRecord.value(record))

        progress.update(maxval)
        progress.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--out', nargs=1, help='Output file')
    parser.add_argument('-e', '--error', nargs='?', help='Error file')
    parser.add_argument('symbols', nargs='+', help='Input files')

    args = parser.parse_args(argv[1:])

    run(args.symbols, args.out[0], args.error)
