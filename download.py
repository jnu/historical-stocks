'''
$ download.py [symbols.txt] [-o/--out data/output.csv]

Get the stocks describe by symbols
'''

from yahoofinance.symbol import Symbol, HistoricalStockRecord
from util import mkdir_p
from sys import argv, stderr
import argparse
import re
import csv
from progressbar import AnimatedMarker, Bar, ETA, Percentage, ProgressBar

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


def run(symbol_files, output_file):
    symbols = parse_symbol_files(symbol_files)

    mkdir_p(output_file)

    widgets = [Percentage(), Bar(marker=RotatingMarker()), ETA()]
    progress = ProgressBar(widgets=widgets, maxval=len(symbols))

    with open(output_file) as fh:
        writer = csv.writer(fh)
        writer.writerow(HistoricalStockRecord.header())

        for i, s in enumerate(symbols):
            progress.update(i)
            sym = Symbol(s)

            try:
                records = sym.get_historical()
            except:
                print >>stderr, "Failed to download:\t%s" % s
                continue

            for record in records:
                writer.writerow(HistoricalStockRecord.value(record))

        progress.update(len(symbols))
        progress.finish()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--out', nargs='1', help='Output file')
    parser.add_argument('symbols', nargs='+', help='Input files')

    args = parser.parse_args(argv[1:])

    run(args.symbols, args.out)
