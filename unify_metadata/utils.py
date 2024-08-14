import os
import json
import dateutil.parser
from .questions import question
import csv
from collections import defaultdict
from datetime import datetime


data_dir = os.path.expanduser('~')+"/.unify-metadata/"

def write_csv(rows,outfile):
    with open(outfile,"w") as fh:
        writer = csv.DictWriter(fh,fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: value if value is not None else "NA" for key, value in row.items()})

def Red(skk): return("\033[91m{}\033[00m" .format(skk))
def Green(skk): return("\033[92m{}\033[00m" .format(skk))
def Yellow(skk): return("\033[93m{}\033[00m" .format(skk))
def LightPurple(skk): return("\033[94m{}\033[00m" .format(skk))
def Purple(skk): return("\033[95m{}\033[00m" .format(skk))
def Cyan(skk): return("\033[96m{}\033[00m" .format(skk))
def LightGray(skk): return("\033[97m{}\033[00m" .format(skk))
def Black(skk): return("\033[98m{}\033[00m" .format(skk))

def get_csv_data(x):
    """Returns a dictionary of column names and values"""
    data = defaultdict(set)
    for row in csv.DictReader(open(x,"r",encoding="utf-8-sig")):
        for k,v in row.items():
            data[k].add(v)
    return data

def find_column(x,columns):
    """Find the column name that is most similar to x"""
    x = x.lower()
    for c in columns:
        if x == c.lower():
            return c
    return None


def get_file_age(path):
    if os.path.exists(path):
        dT = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        return dT.days
    else:
        return 999




def combine_csv_files(args):
    
    columns = defaultdict(int)
    for f in args.files:
        for row in csv.DictReader(open(f)):
            for k in row:
                columns[k] += 1
    
    additional_data = {}
    additional_columns = defaultdict(int)
    if args.additional_data:
        if not args.additional_data_id:
            args.additional_data_id = args.id
        for row in csv.DictReader(open(args.additional_data)):
            additional_data[row[args.additional_data_id]] = row
            for k in row:
                if k not in columns:
                    additional_columns[k] = 1



    rows = []
    for f in args.files:
        for row in csv.DictReader(open(f)):
            new_row = {k:row.get(k,args.missing_value) for k in columns}

            if row[args.id] in additional_data:
                if args.additional_data:
                        for k,v in additional_data[row[args.id]].items():
                            if k in new_row and new_row[k] != args.missing_value:
                                continue
                            new_row[k] = v
                else:
                    for k in additional_data[row[args.id]].keys():
                        if k in new_row:
                            continue
                        new_row[k] = args.missing_value


            rows.append(new_row)


    with open(args.outfile,"w") as fh:
        writer = csv.DictWriter(fh,fieldnames=list(columns)+list(additional_columns))
        writer.writeheader()
        writer.writerows(rows)

def sanitize_location(location):
    lookup = json.load(open(data_dir+"country_lookup.json"))
    if location in lookup:
        return lookup[location]
    else:
        country_code = question(f"Location not found: |{location}|. Please enter manually")
        country_code = country_code.lower()
        if country_code=="none":
            country_code = None
        lookup[location] = country_code
        json.dump(lookup,open(data_dir+"country_lookup.json","w"),indent=4)
        return country_code

def sanitize_date(date,regex=None):
    if date=="not collected":
        return None
    if regex:
        dt = datetime.strptime(date,regex)
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        return float(f'{year}.{int((int(month)/12)*100)}')
    try:
        year = dateutil.parser.parse(date).strftime("%Y")
        month = dateutil.parser.parse(date).strftime("%m")
        return float(f'{year}.{int((int(month)/12)*100)}')
    except:
        userdate = question(f"Could not parse |{date}| as a date. Please enter manually")
        if userdate=="none":
            userdate = None
        return userdate

def left_join_rows(target_rows,source_rows,source_key,target_key):
    fields = list(source_rows[0])
    new_target_rows = target_rows.copy()
    source_rows_dict = { row[source_key]:row for row in source_rows }
    for row in new_target_rows:
        if row[target_key] in source_rows_dict:
            row.update(source_rows_dict[row[target_key]])
        else:
            row.update({ field:None for field in fields })

    return new_target_rows