import cre_defs
from sqlalchemy import UniqueConstraint, ForeignKey, Column, Integer, String, Boolean, create_engine, orm, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from enum import Enum
from collections import namedtuple
import file_utils
import yaml
import logging
import os
import base64

from pprint import pprint

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

    external_id = Column(String, default='')
    description = Column(String, default='')
    name = Column(String)

    is_group = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint(
    name, external_id, name='unique_cre_fields'),)



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

    def __get_external_links(self):
        external_links = []
        all_links = self.session.query(Links).all()
        for link in all_links:
            cre = self.session.query(CRE).filter(CRE.id == link.cre).first()
            standard = self.session.query(Standard).filter(
                Standard.id == link.standard).first()
            external_links.append((cre, standard))
        return external_links

    def __get_internal_links(self):
        internal_links = []
        all_internal_links = self.session.query(InternalLinks).all()
        for il in all_internal_links:
            group = self.session.query(CRE).filter(CRE.id == il.group).first()
            cre = self.session.query(CRE).filter(CRE.id == il.cre).first()
            internal_links.append((group, cre))
        return internal_links

    def find_groups_of_cre(self, cre: CRE):
        """ returns the CREGroups of all the cre groups or none if cre doesn't have groups"""
        cre_id = self.session.query(CRE).filter(
            CRE.name == cre.name).first().id
        links = self.session  .query(InternalLinks).filter(
            InternalLinks.cre == cre_id).all()
        if links:
            result = []
            for link in links:
                result.append(self.session.query(CRE).filter(
                    CRE.id == link.group).first())
            return result

    def find_cres_of_standard(self, standard: Standard):
        db_standard = self.session.query(Standard).filter(and_(Standard.name == standard.name,
                                                               Standard.section == standard.section,
                                                               Standard.subsection == standard.subsection)).first()
        """ returns the CRE or CREGroup of all cres or groups that link to this standard or none if none link to it"""
        if not db_standard:
            return
        links = self.session.query(Links).filter(
            Links.standard == db_standard.id).all()
        if links:
            result = []
            for link in links:
                cre = self.session.query(CRE).filter(
                    CRE.id == link.cre).first()
                result.append(cre)
            return result

    def export(self, dir):
        """ Exports the database to a CRE file collection on disk"""
        # groups = {}
        # groupless_cres = {}
        docs = {}
        group, cre, standard = None, None, None
        groups_written = {}
        cres_written = {}

        # internal links are Group -> CRE
        for link in self.__get_internal_links():
            group = link[0]
            cre = link[1]
            grp = None
            if group.name in docs.keys():
                grp = docs[group.name]
            else:
                grp = GroupfromDB(group)
            grp.add_link(CREfromDB(cre))
            docs[group.name] = grp

        # external links are Group/CRE -> standard
        for link in self.__get_external_links():

            internal_doc = link[0]
            standard = link[1]
            cr = None
            grp = None
            if internal_doc.is_group:  # Group -> standard
                if internal_doc.name in docs.keys():
                    grp = docs[internal_doc.name]
                else:
                    grp = GroupfromDB(internal_doc)
                grp.add_link(StandardFromDB(standard))
                docs[group.name] = grp
            else:  # cre -> standard
                if internal_doc.name in docs.keys():
                    cr = docs[internal_doc.name]
                else:
                    cr = CREfromDB(internal_doc)
            if len(standard.name) != 0:
                cr.add_link(StandardFromDB(standard))
            docs[cr.name] = cr
        for _, doc in docs.items():
            title = doc.name.replace("/", "-")+'.yaml'
            file_utils.writeToDisk(file_title=title,
                                   file_content=yaml.safe_dump(doc.todict()), cres_loc=dir)
        return docs.values()
        # return groups.values(), groupless_cres.values()

    def load(self):
        """ generator, loads db into memory
        TODO:implement?
        no use case still, why would you want the whole db in memory?
        """
        pass

    def add_cre(self, cre: cre_defs.Document):
        is_group = False
        if type(cre).__name__ == cre_defs.CreGroup.__name__:
            is_group = True
        if cre.id != None:
            entry = self.session.query(CRE).filter(
                CRE.name == cre.name, CRE.external_id == cre.id, CRE.is_group == is_group).first()
        else:
            entry = self.session.query(CRE).filter(
                CRE.name == cre.name, CRE.is_group == is_group).first()

        if entry is not None:
            logger.debug("knew of %s ,skipping" % cre.name)

            if is_group:
                logger.debug('knew of group %s:%s' % (cre.name, cre.id))

            return entry
        else:
            logger.debug("did not know of %s ,adding" % cre.name)
            entry = CRE(description=cre.description,
                        name=cre.name, external_id=cre.id,
                        is_group=is_group)
            self.session.add(entry)

        self.session.commit()
        return entry

    def add_standard(self, standard: cre_defs.Standard) -> Standard:
        entry = self.session.query(Standard).filter(and_(Standard.name == standard.name,
                                                         Standard.section == standard.section,
                                                         Standard.subsection == standard.subsection)).first()
        if entry is not None:
            logger.debug("knew of %s:%s ,skipping" %
                         (entry.name, entry.section))
            return entry
        else:
            logger.debug("did not know of %s:%s ,adding" %
                         (standard.name, standard.section))
            entry = Standard(name=standard.name,
                             section=standard.section,
                             subsection=standard.subsection)
            self.session.add(entry)
        self.session.commit()
        return entry

    def add_internal_link(self, group: CRE, cre: CRE):

        if cre.id == None:
            cre = self.session.query(CRE).filter(and_(CRE.name == cre.name,
                                                      CRE.external_id == cre.external_id, CRE.is_group == False)).first()
        if group.id == None:
            if group.external_id == None:
                group = self.session.query(CRE).filter(and_(CRE.name == group.name,
                                                            CRE.is_group == True)).first()
            else:
                group = self.session.query(CRE).filter(and_(CRE.name == group.name,
                                                            CRE.external_id == group.external_id,
                                                            CRE.is_group == True)).first()
        if cre == None or group == None:
            logger.fatal(
                "Tried to insert internal mapping with element that doesn't exist in db, this looks like a bug")
            return
        if self.session.query(InternalLinks).filter(and_(InternalLinks.cre == cre.id, InternalLinks.group == group.id)).count() != 0:
            logger.debug("knew of internal link %s == %s ,skipping" %
                         (cre.name, group.name))
            return
        else:
            logger.debug("did not know of internal link %s:%s == %s:%s ,adding" % (
                group.external_id, group.name, cre.external_id, cre.name))
            self.session.add(InternalLinks(cre=cre.id, group=group.id))
    


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
            logger.debug("knew of link %s:%s==%s ,updating" % (
                standard.name, standard.section, cre.name))
            return
        else:
            logger.debug("did not know of link %s)%s:%s==%s)%s ,adding" % (
                standard.id, standard.name, standard.section, cre.id, cre.name))
            self.session.add(Links(cre=cre.id, standard=standard.id))
        self.session.commit()


def StandardFromDB(dbstandard: Standard):
    return cre_defs.Standard(name=dbstandard.name,
                             section=dbstandard.section,
                             subsection=dbstandard.subsection,
                             hyperlink=dbstandard.link)


def CREfromDB(dbcre: CRE):
    return cre_defs.CRE(name=dbcre.name,
                        description=dbcre.description,
                        id=dbcre.external_id)


def GroupfromDB(dbgroup: CRE):
    return cre_defs.CreGroup(name=dbgroup.name,
                             description=dbgroup.description, id=dbgroup.external_id)
