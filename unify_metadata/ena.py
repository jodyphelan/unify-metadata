import os
import datetime
import subprocess
import csv
from collections import defaultdict
from .questions import question
from .conf import get_default_columns
from .utils import sanitize_location, left_join_rows

data_dir = os.path.expanduser('~')+"/.unify-metadata/"

def update_ena_db(tax_id):
    tax_id = str(tax_id)
    
    if not os.path.isdir(data_dir):
        os.mkdir(data_dir)
    
    runs_file, biosamples_file = get_taxid_files(tax_id)

    if os.path.isfile(runs_file):
        dT = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(runs_file))
        print("ENA list last updates %s days ago..." % dT.days)

    if (not os.path.isfile(runs_file)) or (not os.path.isfile(biosamples_file)) or dT.days>7:
        print("Downloading run file")
        subprocess.call(f"curl -X POST -H \"Content-Type: application/x-www-form-urlencoded\" -d 'result=read_run&query=tax_tree({tax_id})&fields=study_accession%2Csample_accession%2Csecondary_sample_accession%2Crun_accession%2Cinstrument_model%2Clibrary_name%2Clibrary_layout%2Clibrary_strategy%2Cbase_count%2Cexperiment_title%2Cexperiment_alias%2Crun_alias%2Csubmitted_ftp%2Csample_title%2Csample_alias&format=tsv' \"https://www.ebi.ac.uk/ena/portal/api/search\" > {runs_file}",shell=True)
        print("Downloading biosample file")
        subprocess.call(f"curl -X POST -H \"Content-Type: application/x-www-form-urlencoded\" -d 'result=sample&query=tax_tree({tax_id})&fields=sample_accession%2Ccollected_by%2Ccollection_date%2Ccountry%2Cculture_collection%2Cdescription%2Cfirst_public%2Cisolate%2Cisolation_source%2Clocation%2Cstrain%2Ctissue_type%2Csample_alias%2Ccenter_name%2Cenvironment_material%2Cproject_name%2Chost%2Chost_tax_id%2Chost_status%2Chost_sex%2Csubmitted_host_sex%2Chost_body_site%2Cbroker_name%2Csample_title&format=tsv' \"https://www.ebi.ac.uk/ena/portal/api/search\" > {biosamples_file}",shell=True)

def get_taxid_files(tax_id):
    tax_id = str(tax_id)
    return data_dir+tax_id+".runs.txt",data_dir+tax_id+".biosamples.txt"

class RunDB:
    def __init__(self,runs_file,projects=None,project_excluded=None):
        self._sample2ers = defaultdict(set)
        self._ers2proj = {}
        self._ers2err = defaultdict(set)
        self._ers = set()

        for row in csv.DictReader(open(runs_file),delimiter="\t"):
            # skip excluded projects
            if project_excluded and row["study_accession"] in project_excluded: 
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


class BiosampleDB:
    def __init__(self,biosamples_file):
        self._sample2info = {}
        for row in csv.DictReader(open(biosamples_file),delimiter="\t"):
            self._sample2info[row["sample_accession"]] = row

    def get_sample_info(self,sample):
        return self._sample2info[sample]



def generate_data_from_bioprojects(args):
    default_columns = get_default_columns(args.defaults)
    print(default_columns)
    study_name = question("Study name?")
    runs_file,biosamples_file = get_taxid_files(args.taxid)
    rundb = RunDB(runs_file)

    samples = list(*[rundb.get_project_samples(b) for b in args.bioprojects])
    
    sampledb = BiosampleDB(biosamples_file)
    
    country_from_biosamples = [ sampledb.get_sample_info(sample).get("country",None) for sample in samples ]
    if n_missing_country:=country_from_biosamples.count(None)>0:
        country = question(f"There are {n_missing_country} samples are missing country information in biosamples file. Do you want to set a default country?")

        
    

    rows = []
    for sample in samples:
        if len(runs:=rundb.ers2err(sample))==1:
            wgs_id = list(runs)[0]
        else:
            wgs_id = sample
        row = {
            "study_name":study_name,
            "wgs_id":wgs_id,
            "study_accession":rundb.ers2proj(sample),
            "sample_accession":sample,
            "run_accession":";".join(runs),
        }
        biosample = sampledb.get_sample_info(sample)
        for column in default_columns:
            if column in row:
                continue
            elif column in biosample:
                if column in ["country","geographic_source"]:
                    row["country_code"] = sanitize_location(biosample[column])
                else:
                    row[column] = biosample[column]
            elif column=="country" and country:
                row[column] = sanitize_location(country)
            else:
                if column=="wgs_id":
                    print("asjdiao")
                row[column] = None
        rows.append(row)

    if args.additional_data:
        additional_data_rows = [r for r in csv.DictReader(open(args.additional_data),)]
        rows = left_join_rows(rows,additional_data_rows,"wgs_id","wgs_id")
        
    with open(args.outfile,"w") as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        