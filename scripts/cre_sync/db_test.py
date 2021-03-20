import uuid
import yaml
import base64
import os
import unittest
import cre_defs as defs
import db
import tempfile
from pprint import pprint


class TestDB(unittest.TestCase):

    def setUp(self):
        connection = ""  # empty string means temporary db
        collection = db.Standard_collection(cache_file=connection)

        dbcre = db.CRE(description="CREdesc", name="CREname")
        dbgroup = db.CRE(description="Groupdesc",
                         name="GroupName", is_group=True)
        dbstandard = db.Standard(
            subsection="4.5.6", section="FooStand", name="BarStand", link="https://example.com")

        collection.session.add(dbcre)
        collection.session.add(dbgroup)
        collection.session.add(dbstandard)
        collection.session.commit()

        externalLink = db.Links(cre=dbcre.id, standard=dbstandard.id)
        internalLink = db.InternalLinks(cre=dbcre.id, group=dbgroup.id)
        collection.session.add(externalLink)
        collection.session.add(internalLink)
        collection.session.commit()
        self.collection = collection

    def test_export(self):
        # add an internal link, an external link a cre and a standard
        # to simulate group -> cre -> standard connection
        # ensure proper export

        loc = tempfile.mkdtemp()
        result = [defs.CreGroup(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Group, id='', description='Groupdesc',
                                name='GroupName', links=[
                                    defs.CRE(version=defs.CreVersions.V2, doctype=defs.Credoctypes.CRE, id='', description='CREdesc',
                                             name='CREname', links=[], tags=[], metadata=defs.Metadata(labels=[]))
                                ],
                                tags=[], metadata=defs.Metadata(labels=[])),
                  defs.CRE(version=defs.CreVersions.V2, doctype=defs.Credoctypes.CRE, id='', description='CREdesc', name='CREname',
                           links=[
                               defs.Standard(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard, id='', description='', name='BarStand', links=[], tags=[], metadata=defs.Metadata(labels=[]), section='FooStand', subsection='4.5.6', hyperlink='https://example.com')])
                  ]
        self.collection.export(loc)

        # load yamls from loc, parse,
        #  ensure yaml1 is result[0].todict and
        #  yaml2 is result[1].todic
        group = result[0].todict()
        cre = result[1].todict()
        groupname = result[0].name+'.yaml'
        with open(os.path.join(loc, groupname), 'r') as f:
            doc = yaml.safe_load(f)
            self.assertDictEqual(group, doc)
        crename  = result[1].name+'.yaml'
        with open(os.path.join(loc, crename), 'r') as f:
            doc = yaml.safe_load(f)
            self.assertDictEqual(cre, doc)

    def test_StandardFromDB(self):
        expected = defs.Standard(version=defs.CreVersions.V2,
                                 name='foo',
                                 section='bar',
                                 subsection='foobar',
                                 hyperlink='https://example.com/foo/bar')
        self.assertEqual(expected, db.StandardFromDB(db.Standard(
            name='foo', section='bar', subsection='foobar', link='https://example.com/foo/bar')))

    def test_CREfromDB(self):
        c = defs.CRE(id="cid", version=defs.CreVersions.V2, doctype=defs.Credoctypes.CRE,
                     description='CREdesc', name='CREname', links=[])
        self.assertEqual(c, db.CREfromDB(
            db.CRE(external_id="cid", description='CREdesc', name='CREname')))

    def test_GroupfromDB(self):
        g = defs.CreGroup(version=defs.CreVersions.V2,
                          name="g", description='gd', id='gid')
        self.assertEqual(g, db.GroupfromDB(
            db.CRE(external_id='gid', description='gd', name='g', is_group=True)))

    def test_add_cre(self):
        original_desc = uuid.uuid4()
        name = uuid.uuid4()

        c = defs.CRE(id="cid", version=defs.CreVersions.V2, doctype=defs.Credoctypes.CRE,
                     description=original_desc, name=name, links=[])
        emptyCRE = self.collection.session.query(
            db.CRE).filter(db.CRE.name == c.name).first()
        self.assertIsNone(emptyCRE)
        # happy path, add new cre
        newCRE = self.collection.add_cre(c)
        dbcre = self.collection.session.query(db.CRE).filter(
            db.CRE.name == c.name).first()  # ensure transaction happened (commint() called)
        self.assertIsNotNone(dbcre.id)
        self.assertEqual(dbcre.name, c.name)
        self.assertEqual(dbcre.description, c.description)
        self.assertEqual(dbcre.external_id, c.id)
        # ensure the right thing got returned
        self.assertEqual(newCRE.name, c.name)

        # ensure no accidental update (add only adds)
        c.description = "description2"
        newCRE = self.collection.add_cre(c)
        dbcre = self.collection.session.query(db.CRE).filter(
            db.CRE.name == c.name).first()  # ensure transaction happened (commint() called)
        # ensure original description
        self.assertEqual(dbcre.description, str(original_desc))
        # ensure original description
        self.assertEqual(newCRE.description, str(original_desc))

    def test_add_cre(self):
        original_desc = uuid.uuid4()
        name = uuid.uuid4()
        gname = uuid.uuid4()

        c = defs.CRE(id="cid", version=defs.CreVersions.V2, doctype=defs.Credoctypes.CRE,
                     description=original_desc, name=name, links=[])

        g = defs.CreGroup(id="cid", version=defs.CreVersions.V2, doctype=defs.Credoctypes.Group,
                          description=original_desc, name=gname, links=[])

        self.assertIsNone(self.collection.session.query(
            db.CRE).filter(db.CRE.name == c.name).first())
        self.assertIsNone(self.collection.session.query(
            db.CRE).filter(db.CRE.name == g.name).first())

        # happy path, add new cre
        newCRE = self.collection.add_cre(c)
        dbcre = self.collection.session.query(db.CRE).filter(
            db.CRE.name == c.name).first()  # ensure transaction happened (commint() called)
        self.assertIsNotNone(dbcre.id)
        self.assertEqual(dbcre.name, c.name)
        self.assertEqual(dbcre.description, c.description)
        self.assertEqual(dbcre.external_id, c.id)
        # ensure the right thing got returned
        self.assertEqual(newCRE.name, c.name)

        # happy path, add new group
        newGroup = self.collection.add_cre(g)
        dbgroup = self.collection.session.query(db.CRE).filter(
            db.CRE.name == g.name).first()  # ensure transaction happened (commint() called)
        self.assertIsNotNone(dbcre.id)
        self.assertEqual(dbgroup.name, g.name)
        self.assertEqual(dbgroup.is_group, True)
        self.assertEqual(newGroup.is_group, True)

        # ensure no accidental update (add only adds)
        c.description = "description2"
        newCRE = self.collection.add_cre(c)
        dbcre = self.collection.session.query(db.CRE).filter(
            db.CRE.name == c.name).first()  # ensure transaction happened (commint() called)
        # ensure original description
        self.assertEqual(dbcre.description, str(original_desc))
        # ensure original description
        self.assertEqual(newCRE.description, str(original_desc))

    def test_add_standard(self):
        original_section = uuid.uuid4()
        name = uuid.uuid4()

        s = defs.Standard(id="sid", version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard,
                          section=original_section, subsection=original_section, name=name)

        self.assertIsNone(self.collection.session.query(
            db.Standard).filter(db.Standard.name == s.name).first())

        # happy path, add new standard
        newStandard = self.collection.add_standard(s)
        dbstandard = self.collection.session.query(db.Standard).filter(
            db.Standard.name == s.name).first()  # ensure transaction happened (commit() called)
        self.assertIsNotNone(dbstandard.id)
        self.assertEqual(dbstandard.name, s.name)
        self.assertEqual(dbstandard.section, s.section)
        self.assertEqual(dbstandard.subsection, s.subsection)
        # ensure the right thing got returned
        self.assertEqual(newStandard.name, s.name)

        # standards match on all of name,section, subsection <-- if you change even one of them it's a new entry
        
    def test_find_groups_of_cre(self):
        raise NotImplementedError
    
    def test_find_cres_of_standard(self):
        raise NotImplementedError
if __name__ == '__main__':
    unittest.main()
