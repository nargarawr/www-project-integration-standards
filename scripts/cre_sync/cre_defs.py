from pprint import pprint
from dataclasses import dataclass
from enum import Enum
import json
# used for serialising and deserialising yaml CRE documents


class Credoctypes(Enum):
    CRE = "CRE"
    Standard = "Standard"


class LinkTypes(Enum):
    Same = "SAM"

    @classmethod
    def from_str(cls, name):
        if name == "SAM":
            return LinkTypes.Same
        raise ValueError('{} is not a valid link type'.format(name))


@dataclass
class Metadata():
    labels: {}

    def __init__(self, labels={}):
        self.labels = labels

    def todict(self):
        return self.labels


@dataclass
class Link():
    ltype: LinkTypes
    tags: list
    document = None

    def __init__(self, ltype=LinkTypes.Same, tags=[], document=None):
        if document is None:
            raise_MandatoryFieldException('Links need to link to a Document')
        self.document = document
        if type(ltype) == str:
            self.ltype = LinkTypes.from_str(ltype)
        else:
            self.ltype = ltype
        self.tags = tags

    def __eq__(self, other):
        return self.ltype == other.ltype and \
            self.tags == other.tags and \
            self.document == other.document

    def todict(self):
        res = {'type': self.ltype.value}
        if self.document:
            res['document'] = self.document.todict()
        if len(self.tags):
            res['tags'] = self.tags
        return res


@dataclass
class Document():
    doctype: Credoctypes
    id: str
    description: str
    name: str
    links: list
    tags: list
    metadata: Metadata

    def __eq__(self, other):
        return self.id == other.id and \
            self.name == other.name and \
            self.doctype.value == other.doctype.value and \
            self.description == other.description and \
            self.links == other.links and \
            self.tags == other.tags and \
            self.metadata == other.metadata

    def todict(self):
        result = {
            'doctype': self.doctype.value,
            'name': self.name,
        }
        if self.description:
            result['description'] = self.description
        if self.id:
            result['id'] = self.id
        if self.links:
            result['links'] = []
            for link in self.links:
                result['links'].append(link.todict())
        if self.tags:
            result['tags'] = self.tags
        if self.metadata:
            result['metadata'] = self.metadata.todict()
        return result

    def add_link(self, link: Link):
        if not self.links:
            self.links = []
        if type(link).__name__ != Link.__name__:
            raise ValueError("add_link only takes Link() types")

        self.links.append(link)

    def __init__(self, name, doctype=None, id="", description="", links=[], tags=[], metadata: Metadata = None):
        self.description = str(description)
        self.name = str(name) or raise_MandatoryFieldException(
            "Document name not defined for document of doctype %s" % doctype)
        self.links = links
        self.tags = tags
        self.id = id
        self.metadata = metadata
        if not doctype and not self.doctype:
            raise_MandatoryFieldException("You need to set doctype")

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

    def todict(self):
        result = super().todict()
        result['section'] = self.section
        result['subsection'] = self.subsection
        result['hyperlink'] = self.hyperlink
        return result

    def __eq__(self, other):
        return super().__eq__(other) and \
            self.section == other.section and \
            self.subsection == other.subsection and \
            self.hyperlink == other.hyperlink

    def __init__(self, section=None, subsection=None, hyperlink=None, *args, **kwargs):
        self.doctype = Credoctypes.Standard
        if section is None or section=='':
            raise MandatoryFieldException("you can't register an entire standard at once, it needs to have sections")
        self.section = section
        self.subsection = subsection
        self.hyperlink = hyperlink
        super().__init__(*args, **kwargs)


class MandatoryFieldException(Exception):
    pass


def raise_MandatoryFieldException(msg=''): raise MandatoryFieldException(msg)
