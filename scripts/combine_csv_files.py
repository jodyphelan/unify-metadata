#! /usr/bin/env python
import csv
import argparse

parser = argparse.ArgumentParser(description='Combine multiple csv files together',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--source",type=str,help="Raw data file",required=True)
parser.add_argument("--target",type=str,help="Raw data file",required=True)
parser.add_argument("--outfile",type=str,help="Raw data file",required=True)
args = parser.parse_args()


target_rows = [r for r in csv.DictReader(open(args.target))]
source_rows = [r for r in csv.DictReader(open(args.source))]

print(len(target_rows))
print(len(source_rows))

target_columns = list(target_rows[0])
new_source_rows = []
for row in source_rows:
    new_row = {}
    for column in target_columns:
        if column in row:
            new_row[column] = row[column]
        else:
            new_row[column] = ""
    new_source_rows.append(new_row)

with open(args.outfile,"w") as O:
    writer = csv.DictWriter(O,fieldnames=target_columns)
    writer.writeheader()
    writer.writerows(target_rows)
    writer.writerows(new_source_rows)
    