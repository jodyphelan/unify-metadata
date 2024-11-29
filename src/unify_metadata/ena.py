import os
import datetime
import subprocess
import csv
from collections import defaultdict
from .questions import question
from .utils import sanitize_location, sanitize_date, left_join_rows, get_default_columns
import yaml
import json
import dateutil.parser

data_dir = os.path.expanduser('~')+"/.unify-metadata/"

def get_taxid_file_names(tax_id):
    tax_id = str(tax_id)
    return data_dir+tax_id+".runs.txt",data_dir+tax_id+".biosamples.txt"

def update_ena_db(tax_id):
    tax_id = str(tax_id)
    
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)
    
    runs_file, biosamples_file = get_taxid_file_names(tax_id)

    if os.path.isfile(runs_file):
        dT = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(runs_file))
        print("ENA list last updates %s days ago..." % dT.days)

    if (not os.path.isfile(runs_file)) or (not os.path.isfile(biosamples_file)) or dT.days>7:
        print("Downloading run file")
        subprocess.call(f"curl -X POST -H \"Content-Type: application/x-www-form-urlencoded\" -d 'result=read_run&query=tax_tree({tax_id})&fields=study_accession%2Csample_accession%2Csecondary_sample_accession%2Crun_accession%2Cinstrument_model%2Cinstrument_platform%2Clibrary_name%2Clibrary_layout%2Clibrary_strategy%2Cbase_count%2Cexperiment_title%2Cexperiment_alias%2Crun_alias%2Csubmitted_ftp%2Csample_title%2Csample_alias&format=tsv' \"https://www.ebi.ac.uk/ena/portal/api/search\" > {runs_file}",shell=True)
        print("Downloading biosample file")
        subprocess.call(f"curl -X POST -H \"Content-Type: application/x-www-form-urlencoded\" -d 'result=sample&query=tax_tree({tax_id})&fields=sample_accession%2Ccollected_by%2Ccollection_date%2Ccountry%2Cculture_collection%2Cdescription%2Cfirst_public%2Cisolate%2Cisolation_source%2Clocation%2Cstrain%2Ctissue_type%2Csample_alias%2Ccenter_name%2Cenvironment_material%2Cproject_name%2Chost%2Chost_tax_id%2Chost_status%2Chost_sex%2Csubmitted_host_sex%2Chost_body_site%2Cbroker_name%2Csample_title&format=tsv' \"https://www.ebi.ac.uk/ena/portal/api/search\" > {biosamples_file}",shell=True)

    return runs_file,biosamples_file


def get_taxid_files(tax_id):
    return update_ena_db(tax_id)


class RunDB:
    def __init__(self,runs_file,projects=None,project_excluded=None, platform=None):
        self._sample2ers = defaultdict(set)
        self._ers2proj = {}
        self._ers2err = defaultdict(set)
        self._ers = set()

        for row in csv.DictReader(open(runs_file),delimiter="\t"):
            # skip excluded projects
            if project_excluded and row["study_accession"] in project_excluded: 
                continue
            if projects and row["study_accession"] not in projects:
                continue
            if platform and row["instrument_platform"].lower()!=platform.lower():
                continue
            
            self._ers.add(row["sample_accession"])
            
            self._ers2proj[row["sample_accession"]] = row["study_accession"]
            self._sample2ers[row["sample_alias"]].add(row["sample_accession"])
            self._sample2ers[row["library_name"]].add(row["sample_accession"])
            self._sample2ers[row["sample_accession"]].add(row["sample_accession"])
            self._sample2ers[row["secondary_sample_accession"]].add(row["sample_accession"])
            self._sample2ers[row["run_accession"]].add(row["sample_accession"])
            self._ers2err[row["sample_accession"]].add(row["run_accession"])

    def get_project_samples(self,project):
        return [sample for sample in self._ers if self._ers2proj[sample]==project]

    def ers2err(self,ers):
        return self._ers2err[ers]
    
    def ers2proj(self,ers):
        return self._ers2proj[ers]

    def find_sample_accession(self,query):
        if query in self._sample2ers:
            if len(self._sample2ers[query])>1:
                return None
            else:
                return list(self._sample2ers[query])[0]
        else:
            return None
    
    def get_sample_info(self,query):
        info = {}
        sample_acc = self.find_sample_accession(query)
        if sample_acc is None:
            return {
                "sample_accession":None,
                "run_accession":None,
                "study_accession":None,
                "wgs_id":None,
            }
        info["sample_accession"] = sample_acc
        runs = self.ers2err(sample_acc)
        info["run_accession"] = ";".join(runs)
        info["study_accession"] = self.ers2proj(sample_acc)
                                     
        if len(runs)==1:
            info["wgs_id"] = list(runs)[0]
        else:
            info["wgs_id"] = sample_acc
        
        return info


        
class BiosampleDB:
    def __init__(self,biosamples_file):
        self._sample2info = {}
        for row in csv.DictReader(open(biosamples_file),delimiter="\t"):
            self._sample2info[row["sample_accession"]] = row

    def get_sample_info(self,sample):
        result = {
            "sample_accession":None,
            "country_iso3":None,
            "date_of_collection":None,
        }
        if sample not in self._sample2info:
            return result
        raw_info = self._sample2info[sample]
        result["sample_accession"] = raw_info["sample_accession"]
        if "country" in raw_info:
            if raw_info["country"]!="":
                result["country_iso3"] = sanitize_location(raw_info["country"])
        if "location" in raw_info:
            if raw_info["location"]!="":
                result["country_iso3"] = sanitize_location(raw_info["country"])
        if "collection_date" in raw_info:
            if raw_info["collection_date"]!="":
                result["date_of_collection"] = sanitize_date(raw_info["collection_date"],function=dateutil.parser.parse)
        return result



def generate_data_from_bioprojects(args):
    default_columns = get_default_columns(args.defaults)
    project_name = os.path.basename(os.getcwd())
    runs_file,biosamples_file = get_taxid_files(args.taxid)
    rundb = RunDB(runs_file,platform=args.platform)
    samples = []
    for b in args.bioprojects:
        samples += list(rundb.get_project_samples(b))
    
    
    fieldnames = ["id"]
    if args.country:
        args.country = sanitize_location(args.country)
        fieldnames.append("country")

    
    

    with open("raw_data.csv","w") as fh:
        writer = csv.DictWriter(fh,fieldnames=fieldnames)
        writer.writeheader()
        for sample in samples:
            row = {"id":sample}
            if args.country:
                row["country"] = args.country
            writer.writerow(row)
    
    default_columns = list(yaml.safe_load_all(open(args.defaults)))[0]
    mappings = {
        "study_name": project_name,
        "raw_data": "raw_data.csv"
    }

    for element in default_columns:
        if isinstance(element,str):
            mappings[element] = {"column": None}
        else:
            mappings[list(element)[0]] = {"column": None}
    mappings['id'] = {"column":"id"}
    if args.country:
        mappings["country_iso3"] = {"column":"country"}
    json.dump(mappings,open("mappings.conf.json","w"),indent=4)
    
    subprocess.run(f"unify-metadata standardise  --conf mappings.conf.json --raw-data raw_data.csv --find-wgs-id --taxid {args.taxid}",shell=True)