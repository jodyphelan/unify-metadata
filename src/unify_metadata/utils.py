import os
import json
import dateutil.parser
from .questions import question
import csv
from collections import defaultdict
from datetime import datetime
import re
import yaml


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


def get_default_columns(filename):
    conf = list(yaml.safe_load_all(open(filename)))[0]
    columns = []
    for element in conf:
        if isinstance(element,str):
            columns.append(element)
        else:
            columns.append(list(element)[0])
    return columns

def combine_csv_files(args):
    
    if args.defaults:
        columns = get_default_columns(args.defaults)
    else:
        columns = defaultdict(int)
        for f in args.files:
            for row in csv.DictReader(open(f)):
                for k in row:
                    columns[k] += 1
        columns = list(columns)
    
    # additional_data = {}
    # additional_columns = defaultdict(int)
    # if args.additional_data:
    #     if not args.additional_data_id:
    #         args.additional_data_id = args.id
    #     for row in csv.DictReader(open(args.additional_data)):
    #         additional_data[row[args.additional_data_id]] = row
    #         for k in row:
    #             if k not in columns:
    #                 additional_columns[k] = 1


    ena_column_names = ['wgs_id','id','sample_accession','run_accession','study_accession']
    columns = ena_column_names + [c for c in columns if c not in ena_column_names]


    data = defaultdict(dict)
    to_combine = ['id','study_name','raw_data']
    discrepancies = []
    for f in args.files:
        for row in csv.DictReader(open(f)):
            for col in columns:
                if row.get(col,args.missing_value) == args.missing_value:
                    continue
                if col not in data[row[args.id]]:
                    data[row[args.id]][col] = row.get(col,args.missing_value)
                else:
                    if col in to_combine:
                        data[row[args.id]][col] = data[row[args.id]][col] + ";"+row[col]
                    else:
                        if row[col]!=data[row[args.id]][col]:
                            discrepancies.append(f"{row[args.id]}: {col} {data[row[args.id]][col]} != {row[col]}")
                        else:
                            pass

    with open('log.txt','w') as f:
        for d in discrepancies:
            f.write(d+'\n')
    

    rows = []
    for sample_id in data:
        row = {
            args.id:sample_id
        }
        for col in columns:
            row.update({col:data[sample_id].get(col,args.missing_value)})
        rows.append(row)
        

    
    with open(args.outfile,"w") as fh:
        writer = csv.DictWriter(fh,fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)

def sanitize_location(location):
    if location in ("not collected","missing"):
        return None
    if ":" in location:
        location = location.split(":")[0]
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

def sanitize_date(date,regex=None,function=None):
    if date=="not collected":
        return None
    if regex:
        dt = datetime.strptime(date,regex)
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        return float(year) + round(((int(month)-1)/12),2)
    if function:
        try:
            d = function(date)
            year = d.strftime("%Y")
            if re.match(r"^\d{4}$",date):
                month = 7
            else:
                month = d.strftime("%m")
            if int(year)>1000:
                return float(year) + round(((int(month)-1)/12),2)
        except:
            pass
    try:
        if re.match(r"^\d{4}$",date):
            year = dateutil.parser.parse(date).strftime("%Y")
            month = 7
        elif m:=re.match(r"^(\d{4})-(\d{2})-(\d{2})$",date):
            if int(m.group(2))>12: # if the second number is a month
                year = datetime.strptime(date,"%Y-%d-%m").strftime("%Y")
                month = datetime.strptime(date,"%Y-%d-%m").strftime("%m")
            elif int(m.group(3))>12: # if the third number if a month
                year = datetime.strptime(date,"%Y-%m-%d").strftime("%Y")
                month = datetime.strptime(date,"%Y-%m-%d").strftime("%m")
            else:
                raise Exception("Invalid date: "+date)
        else:
            raise Exception("Invalid date: "+date)
        return float(year) + round(((int(month)-1)/12),2)
        
    except:
        lookup = json.load(open(data_dir+"date_lookup.json"))
        if date in lookup:
            return lookup[date]
        userdate = question(f"Could not parse |{date}| as a date. Please enter manually (none)")
        if userdate.lower() in ("none","","n/a","na"):
            userdate = None
        lookup[date] = userdate
        json.dump(lookup,open(data_dir+"date_lookup.json","w"),indent=4)
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