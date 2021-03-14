import cre_defs
from sqlalchemy import UniqueConstraint, ForeignKey, Column, Integer, String, Boolean, create_engine, orm, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from enum import Enum
import file_utils
import yaml
import logging
import os

from pprint import pprint

# class CREDocTypes(Enum):
#     OFFICIAL = "official"
#     PROPOSED = "proposed"
#     LINK = "link"
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
Base = declarative_base()


class Standard(Base):
    __tablename__ = 'standard'
    id = Column(Integer, primary_key=True)
    name = Column(String)  # ASVS or standard name,  what are we linking to
    section = Column(String)  # which part of <name> are we linking to
    subsection = Column(String)  # which subpart of <name> are we linking to

    # some external link to where this is, usually a URL with an anchor
    link = Column(String)
    __table_args__ = (UniqueConstraint(
        name, section, subsection, name='standard_section'),)


class CRE(Base):
    __tablename__ = 'cre'
    id = Column(Integer, primary_key=True)
    # <name> <des> defines <x>,<y>,<z>
    description = Column(String, default='')
    name = Column(String)  # ASVS or standard name,  what are we linking to

    is_group = Column(Boolean, default=False)


class InternalLinks(Base):
    # model cre-groups linking cres
    __tablename__ = 'grouplinks'
    group = Column(Integer, ForeignKey('cre.id'), primary_key=True)
    cre = Column(Integer, ForeignKey('cre.id'), primary_key=True)


class Links(Base):
    __tablename__ = 'links'
    cre = Column(Integer, ForeignKey('cre.id'), primary_key=True)
    standard = Column(Integer, ForeignKey('standard.id'), primary_key=True)


class Standard_collection:
    info_arr: []
    cache: bool
    cache_file: str

    def __init__(self, cache: bool = True, cache_file: str = None, scheme="sqlite:///"):
        self.info_arr = list()
        self.cache = cache
        self.cache_file = cache_file

        if cache:
            self.connect(scheme)
            self.load()

    def connect(self, scheme="sqlite:///"):
        connection = create_engine(scheme+self.cache_file, echo=False)
        Session = sessionmaker(bind=connection)
        self.session = Session()
        Base.metadata.bind = connection

        if not connection.dialect.has_table(connection, Standard.__tablename__):
            Base.metadata.create_all(connection)

    def __get_links(self):
        """ returns a list of tuples of all links in the collection,
            tuple[0] is either the cre/group
            tuple[1] is the standard/cre with full info
        """
        result = []
        all_links = self.session.query(Links).all()
        for link in all_links:
            cre = self.session.query(CRE).filter(CRE.id == link.cre).first()
            standard = self.session.query(Standard).filter(
                Standard.id == link.standard).first()
            result.append((cre, standard))

        all_internal_links = self.session.query(InternalLinks).all()
        for il in all_internal_links:
            group = self.session.query(CRE).filter(
                CRE.id == link.group).first()
            cre = self.session.query(CRE).filter(CRE.id == link.cre).first()
            result.append((group, cre))

        return result

    def find_group_of_cre(self, cre_id: str):
        """ returns the db representation of a cre group or none if it doesn't exist """
        link = self.session.query(InternalLinks).filter(link.cre == cre_id)
        if link:
            return self.session.query(CRE).filter(link.group == cre_id)

    def export(self, dir):
        """ Exports the database to a CRE file collection on disk"""
        groups = {}
        groupless_cres = {}
        group, cre, standard = None, None, None

        for link in self.__get_links():
            if type(link[0]).__name__ == CRE.__name__:
                if link[0].is_group:
                    group = link[0]
                else:
                    cre = link[0]
            elif type(link[1]).__name__ == CRE.__name__:
                cre = link[1]

            if type(link[1]).__name__ == Standard.__name__:
                standard = link[1]

            if group:
                grp = None
                if group.id in groups.keys():
                    grp = groups[group.name]
                else:
                    grp = GroupfromDB(group)
                if len(cre.name) != 0:
                    grp.add_link(CREfromDB(cre))
                if len(standard.name):
                    grp.add_link(StandardFromDB(standard))
                groups[group.id] = grp
                continue
            if cre:
                cr = None
                if cre.id in groupless_cres.keys():
                    cr = groupless_cres[cre.id]
                else:
                    cr = CREfromDB(cre)
                if len(standard.name) != 0:
                    cr.add_link(StandardFromDB(standard))
                groupless_cres[cr.name] = cr

        for _, group in groups.items():
            file_utils.writeToDisk(file_title=group.name,
                                   file_content=yaml.safe_dump(group.__repr__()), cres_loc=dir)
        for _, cre in groupless_cres.items():
            file_utils.writeToDisk(file_title=cre.name,
                                   file_content=yaml.safe_dump(cre.__repr__()), cres_loc=dir)

    def load(self):
        """ generator, loads db into memory
        TODO:implement?
        """
        pass

    def add_cre_group(self, cre: CRE):
        cache_entry = self.session.query(CRE).filter(
            and_(CRE.name == cre.name, CRE.is_group == True)).first()
        if cache_entry is not None:
            logger.debug("knew of %s ,skipping" % cre.name)
            return
        else:
            logger.debug("did not know of %s ,adding" % cre.name)
            cre.is_group = True
            self.session.add(cre)
        self.session.flush()
        self.session.commit()

    def add_cre(self, cre: CRE):
        cache_entry = self.session.query(CRE).filter(
            and_(CRE.name == cre.name)).first()
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
                                                               Standard.subsection == standard.subsection)).first()
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
                and_(CRE.name == cre.name)).first()
        if standard.id == None:
            standard = self.session.query(Standard).filter(and_(
                Standard.name == standard.name,
                Standard.section == standard.section,
                Standard.subsection == standard.subsection)).first()

        cache_entry = self.session.query(Links).filter(
            and_(Links.cre == cre.id, Links.standard == standard.id)).count()
        if cache_entry != 0:
            logger.debug("knew of link %s:%s========%s ,updating" % (
                standard.name, standard.section, cre.name))
            return
        else:
            logger.debug("did not know of link %s)%s:%s=========%s)%s ,adding" % (
                standard.id, standard.name, standard.section, cre.id, cre.name))
            self.session.add(Links(cre=cre.id, standard=standard.id))
        self.session.flush()
        self.session.commit()


def StandardFromDB(dbstandard: Standard):
    return cre_defs.Standard(version=cre_defs.CreVersions.V2.value,
                             name=dbstandard.name,
                             section=dbstandard.section,
                             subsection=dbstandard.subsection,
                             hyperlink=dbstandard.link)


def CREfromDB(dbcre: CRE):
    return cre_defs.CRE(version=cre_defs.CreVersions.V2.value,
                        name=dbcre.name,
                        description=dbcre.description)


def GroupfromDB(dbgroup: CRE):
    return cre_defs.CreGroup(version=cre_defs.CreVersions.V2.value,
                             name=dbgroup.name,
                             description=dbgroup.description)
