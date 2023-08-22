from .ena import update_ena_db

def cli_update_ena_db(args):
    print(args)
    taxid = args.taxid
    update_ena_db(taxid)