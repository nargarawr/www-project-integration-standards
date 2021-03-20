import shutil
import yaml
import os
import argparse
import logging
import uuid
import tempfile
import db
import parsers
from cre_defs import *
from collections import namedtuple
from pprint import pprint
from spreadsheet_utils import readSpreadsheet, createSpreadsheet

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def register_standard(standard: Standard, result: db.Standard_collection):
    linked_standard = result.add_standard(standard)
    for link in standard.links:
        if type(link).__name__ == Standard.__name__:
             # if a standard links another standard it is likely that a standards writer references something
             # in that case, find which of the two standards has at least one CRE attached to it and link both to the parent CRE
            cres = result.find_cres_of_standard(link)
            if cres:
                for cre in cres:
                    result.add_link(cre=cre, link=linked_standard)
            else:
                cres = result.find_cres_of_standard(linked_standard)
                if cres:
                    for cre in cres:
                        result.add_link(cre=cre, link=register_standard(link))
        elif type(link).__name__ == CRE.__name__ or type(link).__name__ == CreGroup.__name__:
            # TODO: what if the CRE applies to all the other standards linked?
            result.add_link(register_cre(link),linked_standard)
    return linked_standard


def register_cre(cre: CRE, result: db.Standard_collection):
    dbcre = result.add_cre(cre)
    for link in cre.links:
        result.add_link(dbcre, register_standard(link, result))
    return dbcre


def parse_file(contents: dict, result: db.Standard_collection):
    """ given yaml from export format add standards to db"""
    if contents.get('doctype') == Credoctypes.CRE.value:
        links = contents.get('links')
        cre = CRE(contents)
        for link in links:
            cre.add_link(link)
        register_cre(cre, result=result)
        return cre
    elif contents.get('doctype') == Credoctypes.Group.value:
        links = contents.get('links')
        group = CreGroup(contents)
        for link in links:
            group.add_link(link)
        register_cre(group, result=result)
        return group
    elif contents.get('doctype') == Credoctypes.Standard.value:
        links = contents.get('links')
        standard = Standard(contents)
        for link in links:
            standard.add_link(link)
        register_standard(standard, result=result)
        return standard


def parse_standards_from_spreadsheeet(cre_file: list, result: db.Standard_collection):
    """ given a yaml with standards, build a list of standards in the db
    """
    groups = {}
    cres = {}
    if "CRE Group 1" in cre_file[0].keys():
        groups, cres = parsers.parse_v1_standards(cre_file)
    else:
        cres = parsers.parse_v0_standards(cre_file)

    # register groupless cres first
    for cre_name, cre in cres.items():
        register_cre(cre, result)

    # groups
    for group_name, group in groups.items():
        dbgroup = result.add_cre(group)

        for document in group.links:
            if type(document).__name__ == CRE.__name__:
                dbcre = register_cre(document, result)
                result.add_internal_link(group=dbgroup, cre=dbcre)

            elif type(document).__name__ == Standard.__name__:
                dbstandard = register_standard(document, result)
                result.add_link(cre=dbgroup, standard=dbstandard)


# this is a library function to be used by other scripts written to specifically parse external mappings
# due to external mappings having special structure, custom parsing will always be needed
def suggest_mapping(known_standard: db.Standard, new_standard: db.Standard, collection: db.Standard_collection):
    """if known_standard in db, find which CRE it's mapped to and add standard b as a link"""
    known_standard = collection.session.query(Standard).filter(_and(Standard.name == known_standard.name,
                                                                    Standard.section == known_standard.section,
                                                                    Standard.subsection == known_standard.subsection)).first()
    new_standard = collection.session.query(Standard).filter(_and(Standard.name == new_standard.name,
                                                                  Standard.section == new_standard.section,
                                                                  Standard.subsection == new_standard.subsection)).first()
    if known_standard and not new_standard:
        collection.add_standard(new_standard)
        new_standard = collection.session.query(Standard).filter(_and(Standard.name == new_standard.name,
                                                                      Standard.section == new_standard.section,
                                                                      Standard.subsection == new_standard.subsection)).first()

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
    pprint(cre_loc)
    for root, directory, cre_docs in os.walk(cre_loc):
        pprint(cre_docs)
        for name in cre_docs:
            pprint(name)
            if name.endswith(".yaml") or name.endswith(".yml"):
                yield os.path.join(root, name)


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
        '--email', help='used in conjuctions with --review, what email to share the resulting spreadsheet with', default="standards_cache.sqlite")
    parser.add_argument(
        '--from_spreadsheet', help='import from a spreadsheet to yaml and then database')
    parser.add_argument(
        '--print-graph', help='will show the graph of the relationships between standards')
    parser.add_argument(
        '--cache_file', help='where to read/store data', default="standards_cache.sqlite")
    parser.add_argument(
        '--cre_loc', help='define location of local cre files, not compatible with --review')

    args = parser.parse_args()

    cache = args.cache_file

    loc = cre_loc

    if args.cre_loc:
        loc = args.cre_loc
    else:
        loc = cre_loc

    if args.review:
        # load the remote spreadsheet to disk,
        # parse the yaml and put into the db without polluting the existing CREs
        loc, cache = prepare_for_review(cache)
    # elif args.add:
        # TODO: read the spreadsheet, use internal parser to parse,<-- how do i find out which parser i need tho?
        #  and add to db and our local cre_loc

    database = db.Standard_collection(cache=True, cache_file=cache)
    if args.from_spreadsheet:
        # write the mappings to disk
        spreadsheet = readSpreadsheet(url=args.from_spreadsheet,
                                      cres_loc=loc, alias="new spreadsheet", validate=False)
        for worksheet, contents in spreadsheet.items():
            parse_standards_from_spreadsheeet(contents, database)

    else:  # not from spreadsheet means parse local yamlfiles
        for file in get_standards_files_from_disk(loc):
            pprint(file)
            with open(file,'rb') as standard:
                parse_file(yaml.safe_load(standard), database)

    docs = database.export(loc)
    spreadsheet = []
    spreadsheet.extend(docs)

    if args.review:
        # create_spreadsheet(spreadsheet, title='cre_review',
        #                    share_with=args.email)
        logger.info("Stored temporary files and database in %s if you want to use them next time, set cache to the location of the database in that dir" % loc)


def create_spreadsheet(spreadsheet: list, title: str, share_with: str):
    """ Reads cres and groups docs exported from a standards_collection.export()
        dumps each doc into a workbook"""
    createSpreadsheet(spreadsheet, title, share_with)


def prepare_for_review(cache):
    loc = tempfile.mkdtemp()
    cache_filename = os.path.basename(cache)
    if os.path.isfile(cache):
        shutil.copy(cache, loc)

    return loc, os.path.join(loc, cache_filename)


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
