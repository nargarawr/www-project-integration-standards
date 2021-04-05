import cre_defs
from sqlalchemy import UniqueConstraint, ForeignKey, Column, Integer, String, Boolean, create_engine, orm, and_, func
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.sql.operators
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
    # which part of <name> are we linking to
    section = Column(String, nullable=False)
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

    __table_args__ = (UniqueConstraint(
        name, external_id, name='unique_cre_fields'),)


class InternalLinks(Base):
    # model cre-groups linking cres
    __tablename__ = 'crelinks'
    type = Column(String, default='SAM')
    group = Column(Integer, ForeignKey('cre.id'), primary_key=True)
    cre = Column(Integer, ForeignKey('cre.id'), primary_key=True)


class Links(Base):
    __tablename__ = 'links'
    type = Column(String, default='SAM')
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
            external_links.append((cre, standard, link.type))
        return external_links

    def __get_internal_links(self):
        internal_links = []
        all_internal_links = self.session.query(InternalLinks).all()
        for il in all_internal_links:
            group = self.session.query(CRE).filter(CRE.id == il.group).first()
            cre = self.session.query(CRE).filter(CRE.id == il.cre).first()
            internal_links.append((group, cre, il.type))
        return internal_links

    def __get_unlinked_standards(self):
        standards = []
        linked_standards = self.session.query(Standard.id).join(Links).filter(Standard.id==Links.standard)
        return self.session.query(Standard).filter(Standard.id.notin_(linked_standards)).all()

    def get_standards_names(self):
        q = self.session.query(Standard.name).distinct().all() # this returns a tuple of (str,nothing)
        res = [i[0] for i in q]
        return res

    def get_max_internal_connections(self):
        count = {}
        q = self.session.query(InternalLinks).all() # TODO: (spyros) this should be made into a count(*) query
        for il in q:
            if il.group in count:
                count[il.group] += 1
            else:
                count[il.group] = 1
            if il.cre in count:
                count[il.cre] += 1
            else: 
                count[il.cre] = 1
        if count:
            return max(count.values())
        else:
            return 0

    def find_cres_of_cre(self, cre: CRE):
        """ returns the higher level CREs of the cre or none if no higher level cres link to it"""
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
        """ returns the CREs that link to this standard or none if none link to it"""
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
        docs = {}
        cre, standard = None, None
        cres_written = {}

        # internal links are Group/HigherLevelCRE -> CRE
        for link in self.__get_internal_links():
            group = link[0]
            cre = link[1]
            type = link[2]
            grp = None
            # when cres link to each other it's a two way link
            # so handle cre1(group) -> cre2 link first
            if group.name in docs.keys():
                grp = docs[group.name]
            else:
                grp = CREfromDB(group)
            grp.add_link(cre_defs.Link(ltype=type, document=CREfromDB(cre)))
            docs[group.name] = grp

            # then handle cre2 -> cre1 link 
            if cre.name in docs.keys():
                c = docs[cre.name]
            else:
                c = CREfromDB(cre)
            docs[cre.name] = c
            c.add_link(cre_defs.Link(ltype=type,document=CREfromDB(group))) # this cannot be grp, grp already has a link to cre2

        # external links are CRE -> standard
        for link in self.__get_external_links():
            internal_doc = link[0]
            standard = link[1]
            type = link[2]
            cr = None
            grp = None
            if internal_doc.name in docs.keys():
                cr = docs[internal_doc.name]
            else:
                cr = CREfromDB(internal_doc)
            if len(standard.name) != 0:
                cr.add_link(cre_defs.Link(
                    ltype=type, document=StandardFromDB(standard)))
            docs[cr.name] = cr

        # unlinked standards last
        for ustandard in self.__get_unlinked_standards():
            ustand = StandardFromDB(ustandard)
            docs["%s-%s:%s"%(ustand.name,ustand.section,ustand.subsection)] = ustand

        for _, doc in docs.items():
            title = doc.name.replace("/", "-")+'.yaml'
            file_utils.writeToDisk(file_title=title,
                                   file_content=yaml.safe_dump(doc.todict()), cres_loc=dir)
        return docs.values()

    def load(self):
        """ generator, loads db into memory
        TODO:implement?
        no use case still, why would you want the whole db in memory?
        """
        pass

    def add_cre(self, cre: cre_defs.CRE):
        if cre.id != None:
            entry = self.session.query(CRE).filter(
                CRE.name == cre.name, CRE.external_id == cre.id).first()
        else:
            entry = self.session.query(CRE).filter(
                CRE.name == cre.name, CRE.description == cre.description).first()

        if entry is not None:
            logger.debug("knew of %s ,skipping" % cre.name)
            return entry
        else:
            logger.debug("did not know of %s ,adding" % cre.name)
            entry = CRE(description=cre.description,
                        name=cre.name, external_id=cre.id)
            self.session.add(entry)
            self.session.commit()
        return entry

    def add_standard(self, standard: cre_defs.Standard) -> Standard:
        entry = self.session.query(Standard).filter(and_(Standard.name == standard.name,
                                                         Standard.section == standard.section,
                                                         Standard.subsection == standard.subsection)).first()
        if entry is not None:
            logger.debug("knew of %s:%s ,updating" %
                         (entry.name, entry.section))
            entry.link = standard.hyperlink
            self.session.commit()
            return entry
        else:
            logger.debug("did not know of %s:%s ,adding" %
                         (standard.name, standard.section))
            entry = Standard(name=standard.name,
                             section=standard.section,
                             subsection=standard.subsection, link=standard.hyperlink)
            self.session.add(entry)
        self.session.commit()
        return entry

    def add_internal_link(self, group: CRE, cre: CRE, type: cre_defs.LinkTypes):
        if cre.id == None:
            if cre.external_id == None:
                cre = self.session.query(CRE).filter(
                    and_(CRE.name == cre.name, CRE.description == cre.description)).first()
            else:
                cre = self.session.query(CRE).filter(
                    and_(CRE.name == cre.name, CRE.external_id == cre.external_id)).first()
        if group.id == None:
            if group.external_id == None:
                group = self.session.query(CRE).filter(
                    and_(CRE.name == group.name, CRE.description == group.description)).first()
            else:
                group = self.session.query(CRE).filter(and_(CRE.name == group.name,
                                                            CRE.external_id == group.external_id)).first()
        if cre == None or group == None:
            logger.fatal(
                "Tried to insert internal mapping with element that doesn't exist in db, this looks like a bug")
            return
        entry = self.session.query(InternalLinks).filter(
            and_(InternalLinks.cre == cre.id, InternalLinks.group == group.id)).first()
        if entry != None:
            logger.debug("knew of internal link %s == %s ,updating" %
                         (cre.name, group.name))
            entry.type = type.value
            self.session.commit()
            return
        else:
            logger.debug("did not know of internal link %s:%s == %s:%s ,adding" % (
                group.external_id, group.name, cre.external_id, cre.name))
            self.session.add(InternalLinks(
                type=type.value, cre=cre.id, group=group.id))

    def add_link(self, cre: CRE, standard: Standard, type: cre_defs.LinkTypes):
        if cre.id == None:
            cre = self.session.query(CRE).filter(
                and_(CRE.name == cre.name)).first()
        if standard.id == None:
            standard = self.session.query(Standard).filter(and_(
                Standard.name == standard.name,
                Standard.section == standard.section,
                Standard.subsection == standard.subsection)).first()

        entry = self.session.query(Links).filter(
            and_(Links.cre == cre.id, Links.standard == standard.id)).first()
        if entry:
            logger.debug("knew of link %s:%s==%s ,updating" % (
                standard.name, standard.section, cre.name))
            entry.type = type.value
            self.session.commit()
            return
        else:
            logger.debug("did not know of link %s)%s:%s==%s)%s ,adding" % (
                standard.id, standard.name, standard.section, cre.id, cre.name))
            self.session.add(
                Links(type=type.value, cre=cre.id, standard=standard.id))
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
