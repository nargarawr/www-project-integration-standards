from pprint import pprint 
from dataclasses import dataclass
from enum import Enum
# used for serialising and deserialising yaml CRE documents


class Credoctypes(Enum):
    Group = 1
    CRE = 2
    Standard = 3


class CreVersions(Enum):
    V0 = 0  # initial experiments, no groups, list of flat mappings
    V1 = 1  # group introduction, still requires manual parsing
    V2 = 2  # future

@dataclass
class Document():
    version: CreVersions
    doctype: Credoctypes
    id: str
    description: str
    name: str
    links: list
    tags: list 

    def __repr__(self):
        result = {'version':self.version.value, 
                'doctype':self.doctype.value,
                'id':self.id,
                'description':self.description,
                'name':self.name,
                'links':[],
                'tags':[]
                }
        for link in self.links:
            result['links'].append(link.__repr__())
        for tag in self.tags:
            result['tags'].append(str(tag))
        return result
    
    def add_link(self, document):
        if self.links == None:
            self.links = []
        self.links.append(document)



    def __init__(self, version, name, doctype=None, id="", description="", links=[], tags=[]):
        self.version = str(version) or raise_MandatoryFieldException(
            "Document version not defined for document %s" % name)
        self.description = str(description)
        self.name = str(name) or raise_MandatoryFieldException(
            "Document name not defined for document of doctype %s" % doctype)
        self.links = [].extend(links)
        self.tags = [].extend(tags)
        self.id = id
    
        if not doctype and not self.doctype:
            raise_MandatoryFieldException("You need to set doctype")


@dataclass
class CreGroup(Document):
    def __init__(self, *args, **kwargs):
        self.doctype = Credoctypes.Group
        super().__init__(*args, **kwargs)


@dataclass
class CRE(Document):
    def __init__(self, *args, **kwargs):
        self.doctype = Credoctypes.CRE
        super().__init__(*args, **kwargs)

 
@dataclass
class Standard(Document):
    doctype = Credoctypes.Standard
    section: str
    subsection: str
    hyperlink: str

    def __init__(self, *args, **kwargs):
        self.doctype = Credoctypes.Standard
        self.section = str(kwargs.pop('section'))
        if 'subsection' in kwargs.keys():
            self.subsection = str(kwargs.pop('subsection'))
        else:
            self.subsection = None
        if 'hyperlink' in kwargs.keys():
            self.hyperlink = str(kwargs.pop('hyperlink'))
        else:
            self.hyperlink = None
        super().__init__(*args, **kwargs)



class MandatoryFieldException(Exception):
    pass


def raise_MandatoryFieldException(msg=''): raise MandatoryFieldException(msg)
