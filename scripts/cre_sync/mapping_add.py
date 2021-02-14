import yaml
import os
import argparse
import logging
import uuid
from collections import namedtuple
from pprint import pprint
from sqlalchemy import UniqueConstraint, ForeignKey, Column, Integer, String, create_engine, orm, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from enum import Enum

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
Base = declarative_base()


class CREDocTypes(Enum):
    OFFICIAL = "official"
    PROPOSED = "proposed"
    LINK = "link"


class Standard(Base):
    __tablename__ = 'standard'
    id = Column(Integer, primary_key=True)
    name = Column(String)  # ASVS or standard name,  what are we linking to
    section = Column(String)  # which part of <name> are we linking to
    subsection = Column(String)  # which subpart of <name> are we linking to

    # some external link to where this is, usually a URL with an anchor
    link = Column(String)
    __table_args__ = (UniqueConstraint(
        name, section,subsection, name='standard_section'),)


class CRE(Base):
    __tablename__ = 'cre'
    id = Column(Integer, primary_key=True)
    # <name> <des> defines <x>,<y>,<z>
    description = Column(String, default='')
    name = Column(String)  # ASVS or standard name,  what are we linking to
    section = Column(String)  # which part of <name> are we linking to
    # some external link to where this is, usually a URL with an anchor
    link = Column(String)
    __table_args__ = (UniqueConstraint(
        name, section, name='cre_section'),)


class Links(Base):
    __tablename__ = 'links'

    cre = Column(Integer, ForeignKey('cre.id'), primary_key=True)
    standard = Column(Integer, ForeignKey('standard.id'), primary_key=True)


class Standard_collection:
    info_arr: []
    cache: bool
    cache_file: str

    def __init__(self, cache: bool = True, cache_file: str = None):
        self.info_arr = list()
        self.cache = cache
        self.cache_file = cache_file

        if cache:
            self.connect()
            self.load()

    def connect(self):
        connection = create_engine('sqlite:///'+self.cache_file, echo=False)
        Session = sessionmaker(bind=connection)
        self.session = Session()
        Base.metadata.bind = connection

        if not connection.dialect.has_table(connection, Standard.__tablename__):
            Base.metadata.create_all(connection)

    def load(self):
        """ generator, loads db into memory
        TODO:implement?
        """
        pass

    def add_cre(self, cre: CRE):
        cache_entry = self.session.query(CRE).filter(
            and_(CRE.name == cre.name, CRE.section == cre.section)).first()
        if cache_entry is not None:
            logger.debug("knew of %s ,skipping" % cre.name)
            return
        else:
            logger.debug("did not know of %s ,adding" % cre.name)
            self.session.add(cre)
        self.session.flush()
        self.session.commit()

    def add_standard(self, standard: Standard):
        cache_entry = self.session.query(Standard).filter(and_(Standard.name == standard.name,
                                                               Standard.section == standard.section,
                                                               Standard.subsection==standard.subsection)).first()
        if cache_entry is not None:
            logger.debug("knew of %s:%s ,skipping" %
                         (cache_entry.name, cache_entry.section))
            return
        else:
            logger.debug("did not know of %s:%s ,adding" %
                         (standard.name, standard.section))
            self.session.add(standard)
        self.session.flush()
        self.session.commit()

    def add_link(self, cre: CRE, standard: Standard):
        if cre.id == None:
            cre = self.session.query(CRE).filter(
                and_(CRE.name == cre.name, CRE.section == cre.section)).first()
        if standard.id == None:
            standard = self.session.query(Standard).filter(and_(
                Standard.name == standard.name,
                Standard.section == standard.section,
                Standard.subsection==standard.subsection)).first()

        cache_entry = self.session.query(Links).filter(
            and_(Links.cre == cre.id, Links.standard == standard.id)).count()
        if cache_entry != 0:
            logger.debug("knew of link %s:%s========%s:%s ,updating" % (
                standard.name, standard.section, cre.name, cre.section))
            return
        else:
            logger.debug("did not know of link %s)%s:%s=========%s)%s:%s ,adding" % (
                standard.id, standard.name, standard.section, cre.id, cre.name, cre.section))
            self.session.add(Links(cre=cre.id, standard=standard.id))
        self.session.flush()
        self.session.commit()


def not_empty(value: str):
    value = str(value)
    return value != None and value != "" and "N/A" not in value


def parse_standards(cre_file: list, status: CREDocTypes, result: Standard_collection):
    """ given a yaml with standards, build a list of standards
    """
    for cre_mapping in cre_file:

        # temporary workaround, the CRE team is the only one adding mappings so everything is official for now
        # when we accept proposed mappings and other links, uncomment:
        # if status == Proposed:
        #   link_status = proposed
        #   cre_status = proposed
        # and change db to have a "proposed status" and change visualisation to paint proposed mappings somehow else

        # so far CRE-ID-lookup-from-taxonomy-table has been used to map CREs
        # so this means that the yaml is "official" and definitely has CRE mapping
        cre = None
        linked_standard = None
        if cre_mapping.get("CRE-ID-lookup-from-taxonomy-table"):
            cre = CRE(description=cre_mapping.pop("Description"),
                      name="CRE",
                      section=cre_mapping.pop("CRE-ID-lookup-from-taxonomy-table"))
            result.add_cre(cre)

        # parse ASVS, the v0 docs have a human-friendly but non-standard way of doing asvs
        if cre_mapping.get("ID-taxonomy-lookup-from-ASVS-mapping"):
            linked_standard = Standard(
                name="ASVS",
                section=cre_mapping.pop(
                    "ID-taxonomy-lookup-from-ASVS-mapping"),
                subsection=cre_mapping.pop("Item")
            )
            result.add_standard(linked_standard)
            result.add_link(cre, linked_standard)

        for key, value in cre_mapping.items():
            if not_empty(value):
                linked_standard = Standard(
                    name=key,
                    section=value
                )
                result.add_standard(linked_standard)
                result.add_link(cre, linked_standard)

# this is a library function to be used by other scripts written to specifically parse external mappings
# due to external mappings having special structure, custom parsing will always be needed


def suggest_mapping(known_standard: Standard, new_standard: Standard, collection: Standard_collection):
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

        if CREDocTypes.OFFICIAL.value in root:
            status = CREDocTypes.OFFICIAL
        elif CREDocTypes.PROPOSED.value in root:
            status = CREDocTypes.PROPOSED
        elif CREDocTypes.LINK.value in root:
            status = CREDocTypes.LINK
        else:
            continue
        for name in cre_docs:
            yield (status, os.path.join(root, name))


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    cre_loc = os.path.join(script_path, "../../cres")

    parser = argparse.ArgumentParser(
        description='Add documents describing standards to a database')
    parser.add_argument(
        '--from_spreadsheet', help='import from a spreadsheet to yaml and then database')
    parser.add_argument(
        '--proposed', help='when used with "--from_spreadsheet" will put the yaml documents in the /proposed/ dir, will still build the local database')
    parser.add_argument(
        '--print-graph', help='will show the graph of the relationships between standards')
    parser.add_argument(
        '--cache_file', help='where to read/store data', default="standards_cache.sqlite")
    args = parser.parse_args()

    cache = args.cache_file
    if args.from_spreadsheet:
        from spreadsheet_to_yaml import readSpreadsheet
        if args.proposed:
            loc = os.path.join(cre_loc, "/proposed")
        else:
            loc = cre_loc
        readSpreadsheet(url=args.from_spreadsheet,
                        cres_loc=loc, alias="new spreadsheet")

    """ for standard yaml in dir parse_standards(file) """
    result = Standard_collection(cache=True, cache_file=cache)

    for status, standard_file in get_standards_files_from_disk(cre_loc):
        with open(standard_file) as standard:
            unparsed = yaml.safe_load(standard)
            parse_standards(unparsed, status, result)


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
