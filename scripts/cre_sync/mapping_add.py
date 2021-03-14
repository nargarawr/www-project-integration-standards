from spreadsheet_utils import readSpreadsheet, createSpreadsheet
import shutil
import yaml
import os
import argparse
import logging
import uuid
import tempfile
import db
import parsers
from collections import namedtuple
from pprint import pprint

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def parse_standards(cre_file: list, result: db.Standard_collection):
    """ given a yaml with standards, build a list of standards in the db
    """
    cres = parsers.parse_v0_standards(cre_file)
    for cre_name, cre in cres.items():
        dbcre = db.CRE(description=cre.description,
                        name=cre.name)
        result.add_cre(dbcre)
        for link in cre.links:
            linked_standard = db.Standard(
                name=link.name,
                section=link.section,
                subsection=link.subsection)
            result.add_standard(linked_standard)
            result.add_link(dbcre, linked_standard)


# this is a library function to be used by other scripts written to specifically parse external mappings
# due to external mappings having special structure, custom parsing will always be needed
def suggest_mapping(known_standard: db.Standard, new_standard: db.Standard, collection: db.Standard_collection):
    """if known_standard in db, find which CRE it's mapped to and add standard b as a link"""
    known_standard = collection.session.query(Standard).filter(_and(Standard.name == known_standard.name,
                                                                    Standard.section == known_standard.section,
                                                                    Standard.subsection==known_standard.subsection)).first()
    new_standard = collection.session.query(Standard).filter(_and(Standard.name == new_standard.name,
                                                                  Standard.section == new_standard.section,
                                                                  Standard.subsection==new_standard.subsection)).first()
    if known_standard and not new_standard:
        collection.add_standard(new_standard)
        new_standard = collection.session.query(Standard).filter(_and(Standard.name == new_standard.name,
                                                                      Standard.section == new_standard.section,
                                                                      Standard.subsection==new_standard.subsection)).first()

        links = collection.session.query(Links).filter(
            and_(Links.standard == known_standard.id))
        for link in links:
            cre = collection.session.query(CRE).filter(
                _and(CRE.id == link.cre.first()))
            collection.add_link(cre=cre, standard=new_standard)

    elif new_standard and not known_standard:
        suggest_mapping(known_standard=new_standard,
                        new_standard=known_standard, collection=collection)
    else:
        logger.fatal("Neither standards exist in the db")


def get_standards_files_from_disk(cre_loc: str):
    result = []
    for root, directory, cre_docs in os.walk(cre_loc):
        status = "OFFICIAL"
        for name in cre_docs:
            yield (status, os.path.join(root, name))


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    cre_loc = os.path.join(script_path, "../../cres")

    parser = argparse.ArgumentParser(
        description='Add documents describing standards to a database')
    parser.add_argument(
        '--add', action='store_true', help='will treat the incoming spreadsheet as a reviewed cre and add to the database')
    parser.add_argument(
        '--review', action='store_true', help='will treat the incoming spreadsheet as a new mapping, will try to map the incoming connections to existing cre\
            and will create a new spreadsheet with the result for review. Nothing will be added to the database at this point')
    parser.add_argument(
        '--from_spreadsheet', help='import from a spreadsheet to yaml and then database')
    parser.add_argument(
        '--print-graph', help='will show the graph of the relationships between standards')
    parser.add_argument(
        '--cache_file', help='where to read/store data', default="standards_cache.sqlite")
    args = parser.parse_args()

    cache = args.cache_file

    loc = ""
    if args.review:
        # load the remote spreadsheet to disk,
        # parse the yaml and put into the db without polluting the existing CREs
        loc, cache = prepare_for_review(cache)
    elif args.add:
        loc = cre_loc
    
    if args.from_spreadsheet:
        # write the mappings to disk
        readSpreadsheet(url=args.from_spreadsheet,
                        cres_loc=loc, alias="new spreadsheet",validate=False)

    # build the db
    result = db.Standard_collection(cache=True, cache_file=cache)
    for status, standard_file in get_standards_files_from_disk(cre_loc):
        with open(standard_file) as standard:
            unparsed = yaml.safe_load(standard)
            parse_standards(unparsed, result)
    
    result.export(loc)

    if args.review:
        create_spreadsheet(result, loc)
        logger.info("Stored temporary files and database in %s if you want to use them next time, set cache to the location of the database in that dir"%loc)

def create_spreadsheet(result:dict, location:str):
    """ Reads cres and groups docs exported from a standards_collection.export()
    loads yaml and dumps each doc into a workbook"""
    return
    raise NotImplementedError()
    createSpreadsheet()

def prepare_for_review(cache):
    loc =  tempfile.mkdtemp()
    cache_filename = os.path.basename(cache)
    shutil.copy(cache, loc)

    return loc, os.path.join(loc,cache_filename)

if __name__ == "__main__":
    main()

# functionality: extract db to yaml
#                ~ import from yaml to db  ~ done
#                yaml to spreadsheet
#                ~visualise connections~ done
#                suggest-mapping (add new link)  <-- todo next
#
# Acceptance criteria:
#   * parse and visualise sylvan's spreadsheet
#   * given a CRE to ASVS mapping and a confidence threshold of 1 and a number of ASVS to X mappings
#   build the rest of sylvan's spreadsheet using repeats of this script
#
# Future work: merge with the github merger/new cre suggester

# ====  new link  ===== (this probs exists in find existing mapping but it's burried under a lot of yaml parsing code)
# select from cre_links join standards where cre_links.standard_id = standards.standard_id
# for cre_id_links in result:
#   confidence = 0
#   for standard in cre_id_links:
#       if standard in link:
#           confidence++
#   if confidence >= GLOBAL_CONFIDENCE_THRESHOLD:
#       add_link(new_link,cre_id_links.cre_id)
#   else:
#       prod_for_human_review(link)
#
