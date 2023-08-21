import json
import sys
import argparse
import csv
from collections import defaultdict
import yaml
import dateutil.parser
import os
import subprocess as sp
import datetime 
from .questions import multiple_choice

__version__ = "0.1.0"

from .ena import *

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

def get_mapping_skeleton(args):
    standard_columns = list(yaml.safe_load_all(open(args.defaults)))[0]

    csv_data = get_csv_data(args.raw_data)

    csv_columns = list(csv_data)
    conf = {}

    study_name = input(Cyan("What is the study name?\n"))
    conf["study_name"] = study_name



    for element in standard_columns:
        print("------ " + Green(str(element)) + " ------")
        happy = False
        while not happy:
            if isinstance(element,str):
                c = element
            else:
                c = list(element)[0]

            tmp_c = find_column(c,csv_columns)
            if tmp_c:
                sys.stderr.write(f"Found column {tmp_c} for {c}\n")
                data_column = tmp_c
            else:
                i = input(Cyan(f"What is the mapping for {c}? (leave blank to skip)\n") + "\n".join([f"{i+1}) {x}" for i,x in enumerate(csv_columns)]) + "\n")
                if i=="":
                    data_column = None
                else:
                    data_column = csv_columns[int(i)-1]


            tmp_conf = {"column":data_column}
            
            if data_column is None:
                break

            mapping =  {}

            if "values" in element:
                values = element["values"]
                for v in sorted(csv_data[data_column]):
                    question = f"What is the mapping for {v}?"
                    mapping[v] = multiple_choice(question,values)
                tmp_conf["mapping"] = mapping

            if "date" in element:
                for v in csv_data[data_column]:
                    try:
                        tmpdate = dateutil.parser.parse(v).strftime(element["date"])
                        mapping[v] = tmpdate
                    except:
                        userdate = input(f"Could not parse {v} as a date. Press manually enter to value continue\n")
                        mapping[v] = userdate
                tmp_conf["mapping"] = mapping
            
            
            qhappy = input(f"Are you happy with this mapping for {data_column}? {Green(str(tmp_conf))} (Y/n)\n")
            if qhappy=="y" or  qhappy=="":
                happy = True  

        conf[c] = tmp_conf
        print("\n#####################\n")

    with open(args.outfile,"w") as fh:
        json.dump(conf,fh,indent=4)

def get_file_age(path):
    if os.path.exists(path):
        dT = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(path))
        return dT.days
    else:
        return 999

def standardise_raw_data(args):
    conf = json.load(open(args.conf))

    rows = []

    for row in csv.DictReader(open(args.raw_data,"r",encoding="utf-8-sig")):
        if row[conf["id"]["column"]]=="NA":continue
        new_row = {"id":row[conf["id"]["column"]]}
        for key in conf:
            if isinstance(conf[key],str):
                new_row[key] = conf[key]
            elif isinstance(conf[key],dict):
                if conf[key]['column'] is None:
                    new_row[key] = "NA"
                elif "mapping" in conf[key]:
                    new_row[key] = conf[key]["mapping"][row[conf[key]["column"]]]
                else:
                    new_row[key] = row[conf[key]["column"]]
        rows.append(new_row)

    with open(args.outfile,"w") as fh:
        writer = csv.DictWriter(fh,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def parse_run_data(path,projects=None,project_blacklist=None):
    tmp_sample2err = defaultdict(set)
    tmp_sample2ers = defaultdict(set)
    sample_accession2err = defaultdict(set)
    sample2prj = {}
    err_ignore_sample = []
    err2prj = {}
    print("Loading run file")
    for row in csv.DictReader(open(args.run_file),delimiter="\t"):
        if projects and row["study_accession"] not in project: continue
        if project_blacklist and row["study_accession"] in project_blacklist: continue
        if row["sample_alias"]=="" and row["library_name"]=="": continue

        sample2prj[row["sample_accession"]] = row["study_accession"]
        tmp_sample2err[row["sample_alias"]].add(row["run_accession"])
        tmp_sample2ers[row["sample_alias"]].add(row["sample_accession"])
        tmp_sample2err[row["library_name"]].add(row["run_accession"])
        tmp_sample2ers[row["library_name"]].add(row["sample_accession"])
        tmp_sample2err[row["sample_accession"]].add(row["run_accession"])
        tmp_sample2ers[row["sample_accession"]].add(row["sample_accession"])
        tmp_sample2err[row["secondary_sample_accession"]].add(row["run_accession"])
        tmp_sample2ers[row["secondary_sample_accession"]].add(row["sample_accession"])
        tmp_sample2err[row["run_accession"]].add(row["run_accession"])
        tmp_sample2ers[row["run_accession"]].add(row["sample_accession"])
        sample_accession2err[row["sample_accession"]].add(row["run_accession"])
        err2prj[row["run_accession"]] = row["study_accession"]
        if row["study_accession"] in err_projects:
            err_ignore_sample.append(row["run_accession"])

    sample2err = {}
    sample2ers = {}
    err2sample_accession = {}
    for s in tmp_sample2err:
        sample2err[s] = "_".join(sorted(tmp_sample2err[s]))
        sample2ers[s] = "_".join(sorted(tmp_sample2ers[s]))



def test(args):
    standardise_raw_data(args)


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