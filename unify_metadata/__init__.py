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

__version__ = "0.1.0"

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
                    break
                else:
                    data_column = csv_columns[int(i)-1]
            if data_column=="":
                continue


            tmp_conf = {"column":data_column}

            mapping =  {}

            if "values" in element:
                values = element["values"]
                for v in sorted(csv_data[data_column]):
                    i = input(
                        f"What is the mapping for {v}?\n" + "\n".join([f"{i+1}) {x}" for i,x in enumerate(values)]) + "\n"
                    )
                    mapping[v] = values[int(i)-1]
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
                if "mapping" in conf[key]:
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
    err2sample = {}
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


def download_sra_data(taxid):
    home = os.path.expanduser("~")
    run_file = f"{home}/.unify_metadata/{taxid}.runs.txt"
    samples_file = f"{home}/.unify_metadata/{taxid}.samples.txt"
    if not os.path.exists(f"{home}/.unify_metadata"):
        os.mkdir(f"{home}/.unify_metadata")
    if get_file_age(run_file)>7:
        print("Downloading runs file")
        sp.call(f"curl -X POST -H \"Content-Type: application/x-www-form-urlencoded\" -d 'result=read_run&query=tax_tree({taxid})&fields=study_accession%2Csample_accession%2Csecondary_sample_accession%2Crun_accession%2Cinstrument_model%2Clibrary_name%2Clibrary_layout%2Clibrary_strategy%2Cbase_count%2Cexperiment_title%2Cexperiment_alias%2Crun_alias%2Csubmitted_ftp%2Csample_title%2Csample_alias&format=tsv' \"https://www.ebi.ac.uk/ena/portal/api/search\" > {run_file}",shell=True)
    if get_file_age(samples_file)>7:
        print("Downloading samples file")
        sp.call(f"curl -X POST -H \"Content-Type: application/x-www-form-urlencoded\" -d 'result=sample&query=tax_tree(77643)&fields=sample_accession%2Ccollected_by%2Ccollection_date%2Ccountry%2Cculture_collection%2Cdescription%2Cfirst_public%2Cisolate%2Cisolation_source%2Clocation%2Cstrain%2Ctissue_type%2Csample_alias%2Ccenter_name%2Cenvironment_material%2Cproject_name%2Chost%2Chost_tax_id%2Chost_status%2Chost_sex%2Csubmitted_host_sex%2Chost_body_site%2Cbroker_name%2Csample_title&format=tsv' \"https://www.ebi.ac.uk/ena/portal/api/search\" > {samples_file}",shell=True)

def test(args):
    standardise_raw_data(args)