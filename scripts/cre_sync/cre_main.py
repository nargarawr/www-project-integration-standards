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


def register_standard(standard: Standard, collection: db.Standard_collection)->db.Standard:
    """ for each link find if either the root standard or the link have a CRE, then map the one who doesn't to the CRE
        if both don't map to anything, just add them in the db as unlinked standards
    """
    linked_standard = collection.add_standard(standard)
    cre_less_standards = []
    cres_added = [] # we need to know the cres added in case we encounter a group, then we get the group to link to these cres
    groups_added = []
    for link in standard.links:
        if type(link).__name__ == Standard.__name__:
            # if a standard links another standard it is likely that a standards writer references something
            # in that case, find which of the two standards has at least one CRE attached to it and link both to the parent CRE
            cres = collection.find_cres_of_standard(link)
            if cres:
                for cre in cres:
                    collection.add_link(cre=cre, link=linked_standard)
                    for unlinked_standard in cre_less_standards: # if anything in this 
                        collection.add_link(cre=cre, link=unlinked_standard)
            else:
                cres = collection.find_cres_of_standard(linked_standard)
                if cres:
                    for cre in cres:
                        collection.add_link(cre=cre, standard=collection.add_standard(link))
                        for unlinked_standard in cre_less_standards:
                            collection.add_link(cre=cre, standard=unlinked_standard)
                else: # if neither the root nor a linked standard has a CRE, add both as unlinked standards
                    collection.add_standard(link)
                    cre_less_standards.append(link)
        elif type(link).__name__ == CRE.__name__ :
            dbcre = register_cre(link,collection)
            collection.add_link(dbcre, linked_standard)
            cres_added.append(dbcre)
        elif type(link).__name__ == CreGroup.__name__:
            dbgroup = register_cre(link,collection)
            collection.add_link(dbgroup, linked_standard)
            groups_added.append(dbgroup)
    for group in groups_added:
        for cre in cres_added:
            collection.add_internal_link(cre=cre,group=group)
    return linked_standard


def register_cre(cre: CRE, result: db.Standard_collection)->db.CRE:
    dbcre = result.add_cre(cre)
    for link in cre.links:
        result.add_link(dbcre, register_standard(link, result))
    return dbcre

def parse_cre_file_link(link:dict)->(Document,[]):
    if link.get('doctype') ==Credoctypes.CRE.value:
        links = link.pop('links')
        cre = CRE(**link)
        return cre,links
    elif link.get('doctype') ==Credoctypes.Group.value:
        links = link.pop('links')
        group = CreGroup(**link)
        return group,links
    elif link.get('doctype') ==Credoctypes.Standard.value:
        links = link.pop('links')
        standard = Standard(**link)
        return standard,links


def parse_file(contents: dict, result: db.Standard_collection)->Document:
    """ given yaml from export format add standards to db"""
    if contents.get('doctype') == Credoctypes.CRE.value:
        links = contents.pop('links')
        cre = CRE(**contents)
        for link in links:
            l, _ = parse_cre_file_link(link) # TODO: recurse and register potential links of links
            cre.add_link(l)
        register_cre(cre, result=result)
        return cre
    elif contents.get('doctype') == Credoctypes.Group.value:
        links = contents.get('links')
        group = CreGroup(contents)
        for link in links:
            l, _ = parse_cre_file_link(link) # TODO: recurse and register potential links of links
            group.add_link(l)
        register_cre(group, result=result)
        return group
    elif contents.get('doctype') == Credoctypes.Standard.value:
        links = contents.get('links')
        standard = Standard(contents)
        for link in links:
            l, _ = parse_cre_file_link(link) # TODO: recurse and register potential links of links
            standard.add_link(l)
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
    for root, _, cre_docs in os.walk(cre_loc):
        for name in cre_docs:
            if name.endswith(".yaml") or name.endswith(".yml"):
                yield os.path.join(root, name)


def add_from_spreadsheet(spreadsheet_url: str, cache_loc: str, cre_loc: str):
    """ --add --from_spreadsheet <url>
        use the cre db in this repo
        import new mappings from <url>
        export db to ../../cres/
    """
    database = db.Standard_collection(cache=True, cache_file=cache_loc)
    spreadsheet = readSpreadsheet(url=spreadsheet_url, cres_loc=cre_loc, alias="new spreadsheet", validate=False)
    for worksheet, contents in spreadsheet.items():
        parse_standards_from_spreadsheeet(contents, database)
    docs = database.export(cre_loc)


def add_from_disk(cache_loc: str, cre_loc: str):
    """ --add --cre_loc <path>
        use the cre db in this repo
        import new mappings from <path>
        export db to ../../cres/
    """
    database = db.Standard_collection(cache=True, cache_file=cache_loc)
    for file in get_standards_files_from_disk(cre_loc):
        with open(file, 'rb') as standard:
            parse_file(yaml.safe_load(standard), database)
    docs = database.export(cre_loc)


def review_from_spreadsheet(cache:str, spreadsheet_url: str,share_with:str):
    """ --review --from_spreadsheet <url>
        copy db to new temp dir,
        import new mappings from spreadsheet
        export db to tmp dir
        create new spreadsheet of the new CRE landscape for review 
    """
    # last one is TODO:
    loc, cache = prepare_for_review(cache)
    database = db.Standard_collection(cache=True, cache_file=cache)
    spreadsheet = readSpreadsheet(url=spreadsheet_url,
                                  cres_loc=loc, alias="new spreadsheet", validate=False)
    for worksheet, contents in spreadsheet.items():
        parse_standards_from_spreadsheeet(contents, database)
    docs = database.export(loc)
    spreadsheet = []
    spreadsheet.extend(docs)

    # create_spreadsheet(spreadsheet, title='cre_review', share_with=args.email)
    logger.info("Stored temporary files and database in %s if you want to use them next time, set cache to the location of the database in that dir" % loc)


def review_from_disk(cache:str, cre_file_loc: str,share_with:str):
    """ --review --cre_loc <path>
        copy db to new temp dir,
        import new mappings from yaml files defined in <cre_loc>
        export db to tmp dir
        create new spreadsheet of the new CRE landscape for review 
    """
   # last one is TODO:
    loc, cache = prepare_for_review(cache)
    database = db.Standard_collection(cache=True, cache_file=cache)
    for file in get_standards_files_from_disk(cre_file_loc):
        with open(file, 'rb') as standard:
            parse_file(yaml.safe_load(standard), database)

    docs = database.export(loc)
    spreadsheet = []
    spreadsheet.extend(docs)
    # create_spreadsheet(spreadsheet, title='cre_review', share_with=args.email)
    logger.info("Stored temporary files and database in %s if you want to use them next time, set cache to the location of the database in that dir" % loc)

def print_graph():
    """export db to single json object, pass to visualise.html so it can be shown in browser"""
    raise NotImplementedError

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
        '--print_graph', help='will show the graph of the relationships between standards')
    parser.add_argument(
        '--cache_file', help='where to read/store data', default="standards_cache.sqlite")
    parser.add_argument(
        '--cre_loc', default=os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../cres"), help='define location of local cre files for review/add')

    args = parser.parse_args()
    if args.review and args.from_spreadsheet:
        review_from_spreadsheet(cache=args.cache_file, spreadsheet_url=args.from_spreadsheet,share_with=args.email)
    elif args.review and args.cre_loc:
        review_from_disk(cache=args.cache_file, cre_file_loc=args.cre_loc, share_with=args.email)
    elif args.add and args.from_spreadsheet:
        add_from_spreadsheet(spreadsheet_url=args.spreadsheet,cache_loc=args.cache_file,cre_loc=args.cre_loc)
    elif args.add and args.cre_loc and not args.from_spreadsheet:
        add_from_disk(cache_loc=args.cache_file,cre_loc=args.cre_loc)
    elif args.print_graph:
        print_graph()

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

# functionality: extract db to yaml ~ done
#                ~ import from yaml to db  ~ done
#                yaml to spreadsheet
#                ~visualise connections~ done
#                suggest-mapping (add new link) ~ done
#
# Acceptance criteria:
#   * parse and visualise sylvan's spreadsheet done
#   * given a CRE to ASVS mapping and a confidence threshold of 1 and a number of ASVS to X mappings
#   build the rest of sylvan's spreadsheet using repeats of this script
#
# Future work: merge with the github merger/new cre suggester
