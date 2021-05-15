import base64
import copy
import os
import tempfile
import unittest
import uuid
from pprint import pprint
from unittest import skip

import yaml

from application import create_app, sqla
from application.database import db
from application.defs import cre_defs as defs


class TestDB(unittest.TestCase):

    def tearDown(self):
        sqla.session.remove()
        sqla.drop_all()
        self.app_context.pop()

    def setUp(self):
        self.app = create_app(mode='test')
        sqla.create_all(app=self.app)

        self.app_context = self.app.app_context()
        self.app_context.push()
        self.collection = db.Standard_collection()
        collection = self.collection

        dbcre = db.CRE(description="CREdesc", name="CREname")
        dbgroup = db.CRE(description="Groupdesc", name="GroupName")
        dbstandard = db.Standard(
            subsection="4.5.6",
            section="FooStand",
            name="BarStand",
            link="https://example.com",
        )

        unlinked = db.Standard(
            subsection="4.5.6",
            section="Unlinked",
            name="Unlinked",
            link="https://example.com",
        )

        collection.session.add(dbcre)

        collection.session.add(dbgroup)

        collection.session.add(dbstandard)

        collection.session.add(unlinked)
        collection.session.commit()

        externalLink = db.Links(cre=dbcre.id, standard=dbstandard.id)
        internalLink = db.InternalLinks(cre=dbcre.id, group=dbgroup.id)
        collection.session.add(externalLink)
        collection.session.commit()

        collection.session.add(internalLink)
        collection.session.commit()

        self.collection = collection

    def test_get_by_tags(self):
        """
        Given: A CRE with no links and a combination of possible tags:
                    "tag1,dash-2,underscore_3,space 4,co_mb-ination%5"
               A Standard with no links and a combination of possible tags
                    "tag1, dots.5.5, space 6 , several spaces and newline          7        \n"
               some limited overlap between the tag-sets
        Expect:
               The CRE to be returned when searching for "tag-2" and for ["tag1","underscore_3"]
               The Standard to be returned when searching for "space 6" and ["dots.5.5", "space 6"]
               Both to be returned when searching for "space" and "tag1"
        """

        dbcre = db.CRE(
            description="tagCREdesc1",
            name="tagCREname1",
            tags="tag1,dash-2,underscore_3,space 4,co_mb-ination%5",
        )
        cre = db.CREfromDB(dbcre)
        cre.id = ""
        dbstandard = db.Standard(
            subsection="4.5.6.7",
            section="tagsstand",
            name="tagsstand",
            link="https://example.com",
            tags="tag1, dots.5.5, space 6 , several spaces and newline          7        \n",
        )
        standard = db.StandardFromDB(dbstandard)
        self.collection.session.add(dbcre)
        self.collection.session.add(dbstandard)
        self.collection.session.commit()

        self.maxDiff = None
        self.assertEqual(self.collection.get_by_tags(["dash-2"]), [cre])
        self.assertEqual(self.collection.get_by_tags(
            ["tag1", "underscore_3"]), [cre])
        self.assertEqual(self.collection.get_by_tags(["space 6"]), [standard])
        self.assertEqual(
            self.collection.get_by_tags(["dots.5.5", "space 6"]), [standard]
        )

        self.assertCountEqual(
            [cre, standard], self.collection.get_by_tags(["space"]))
        self.assertCountEqual(
            [cre, standard], self.collection.get_by_tags(["space", "tag1"])
        )
        self.assertCountEqual(
            self.collection.get_by_tags(["tag1"]), [cre, standard])

        self.assertEqual(self.collection.get_by_tags([]), [])
        self.assertEqual(self.collection.get_by_tags(
            ["this should not be a tag"]), [])

    def test_get_standards_names(self):
        result = self.collection.get_standards_names()
        expected = ["BarStand", "Unlinked"]
        self.assertEqual(expected, result)

    def test_get_max_internal_connections(self):
        self.assertEqual(self.collection.get_max_internal_connections(), 1)

        dbcrelo = db.CRE(name='internal connections test lo',
                         description='ictlo')
        dbcrehi = db.CRE(name='internal connections test hi',
                         description='icthi')
        self.collection.session.add(dbcrelo)
        self.collection.session.add(dbcrehi)
        self.collection.session.commit()
        for i in range(0, 100):
            dbcre = db.CRE(name=str(i)+' name', description=str(i)+' desc')
            self.collection.session.add(dbcre)
            self.collection.session.commit()

            # 1 low level cre to multiple groups
            self.collection.session.add(
                db.InternalLinks(group=dbcre.id, cre=dbcrelo.id))

            # 1 hi level cre to multiple low level
            self.collection.session.add(
                db.InternalLinks(group=dbcrehi.id, cre=dbcre.id))

            self.collection.session.commit()

        result = self.collection.get_max_internal_connections()
        self.assertEqual(result, 100)

    def test_export(self):
        """
        Given:
            A CRE "CREname" that links to a CRE "GroupName" and a Standard "BarStand"
        Expect:
            2 documents on disk, one for "CREname"
            with a link to "BarStand" and "GroupName" and one for "GroupName" with a link to "CREName"
        """
        loc = tempfile.mkdtemp()
        result = [
            defs.CRE(
                description="Groupdesc",
                name="GroupName",
                links=[
                    defs.Link(document=defs.CRE(
                        description="CREdesc", name="CREname"))
                ],
            ),
            defs.CRE(
                id="",
                description="CREdesc",
                name="CREname",
                links=[
                    defs.Link(
                        document=defs.CRE(
                            description="Groupdesc", name="GroupName")
                    ),
                    defs.Link(
                        document=defs.Standard(
                            name="BarStand",
                            section="FooStand",
                            subsection="4.5.6",
                            hyperlink="https://example.com",
                        )
                    ),
                ],
            ),
            defs.Standard(
                subsection="4.5.6",
                section="Unlinked",
                name="Unlinked",
                hyperlink="https://example.com",
            ),
        ]
        self.collection.export(loc)

        # load yamls from loc, parse,
        #  ensure yaml1 is result[0].todict and
        #  yaml2 is result[1].todic
        group = result[0].todict()
        cre = result[1].todict()
        groupname = result[0].name + ".yaml"
        with open(os.path.join(loc, groupname), "r") as f:
            doc = yaml.safe_load(f)
            self.assertDictEqual(group, doc)
        crename = result[1].name + ".yaml"
        with open(os.path.join(loc, crename), "r") as f:
            doc = yaml.safe_load(f)
            self.assertDictEqual(cre, doc)

    def test_StandardFromDB(self):
        expected = defs.Standard(
            name="foo",
            section="bar",
            subsection="foobar",
            hyperlink="https://example.com/foo/bar",
        )
        self.assertEqual(
            expected,
            db.StandardFromDB(
                db.Standard(
                    name="foo",
                    section="bar",
                    subsection="foobar",
                    link="https://example.com/foo/bar",
                )
            ),
        )

    def test_CREfromDB(self):
        c = defs.CRE(
            id="cid",
            doctype=defs.Credoctypes.CRE,
            description="CREdesc",
            name="CREname",
        )
        self.assertEqual(
            c,
            db.CREfromDB(
                db.CRE(external_id="cid", description="CREdesc", name="CREname")
            ),
        )

    def test_add_group(self):
        original_desc = str(uuid.uuid4())
        name = str(uuid.uuid4())
        gname = str(uuid.uuid4())

        c = defs.CRE(
            id="cid", doctype=defs.Credoctypes.CRE, description=original_desc, name=name
        )

        g = defs.CRE(
            id="cid",
            doctype=defs.Credoctypes.CRE,
            description=original_desc,
            name=gname,
        )

        self.assertIsNone(
            self.collection.session.query(db.CRE).filter(
                db.CRE.name == c.name).first()
        )
        self.assertIsNone(
            self.collection.session.query(db.CRE).filter(
                db.CRE.name == g.name).first()
        )

        # happy path, add new cre
        newCRE = self.collection.add_cre(c)
        dbcre = (
            self.collection.session.query(db.CRE).filter(
                db.CRE.name == c.name).first()
        )  # ensure transaction happened (commint() called)
        self.assertIsNotNone(dbcre.id)
        self.assertEqual(dbcre.name, c.name)
        self.assertEqual(dbcre.description, c.description)
        self.assertEqual(dbcre.external_id, c.id)
        # ensure the right thing got returned
        self.assertEqual(newCRE.name, c.name)

        # happy path, add new group
        newGroup = self.collection.add_cre(g)
        dbgroup = (
            self.collection.session.query(db.CRE).filter(
                db.CRE.name == g.name).first()
        )  # ensure transaction happened (commint() called)
        self.assertIsNotNone(dbcre.id)
        self.assertEqual(dbgroup.name, g.name)
        self.assertEqual(dbgroup.description, g.description)

        # ensure no accidental update (add only adds)
        c.description = "description2"
        newCRE = self.collection.add_cre(c)
        dbcre = (
            self.collection.session.query(db.CRE).filter(
                db.CRE.name == c.name).first()
        )  # ensure transaction happened (commint() called)
        # ensure original description
        self.assertEqual(dbcre.description, str(original_desc))
        # ensure original description
        self.assertEqual(newCRE.description, str(original_desc))

    def test_add_standard(self):
        original_section = str(uuid.uuid4())
        name = str(uuid.uuid4())

        s = defs.Standard(
            id="sid",
            doctype=defs.Credoctypes.Standard,
            section=original_section,
            subsection=original_section,
            name=name,
        )

        self.assertIsNone(
            self.collection.session.query(db.Standard)
            .filter(db.Standard.name == s.name)
            .first()
        )

        # happy path, add new standard
        newStandard = self.collection.add_standard(s)
        dbstandard = (
            self.collection.session.query(db.Standard)
            .filter(db.Standard.name == s.name)
            .first()
        )  # ensure transaction happened (commit() called)
        self.assertIsNotNone(dbstandard.id)
        self.assertEqual(dbstandard.name, s.name)
        self.assertEqual(dbstandard.section, s.section)
        self.assertEqual(dbstandard.subsection, s.subsection)
        # ensure the right thing got returned
        self.assertEqual(newStandard.name, s.name)

        # standards match on all of name,section, subsection <-- if you change even one of them it's a new entry

    def find_cres_of_cre(self):
        dbcre = db.CRE(description="CREdesc1", name="CREname1")
        groupless_cre = db.CRE(description="CREdesc2", name="CREname2")
        dbgroup = db.CRE(description="Groupdesc1", name="GroupName1")
        dbgroup2 = db.CRE(description="Groupdesc2", name="GroupName2")

        only_one_group = db.CRE(description="CREdesc3", name="CREname3")

        self.collection.session.add(dbcre)
        self.collection.session.add(groupless_cre)
        self.collection.session.add(dbgroup)
        self.collection.session.add(dbgroup2)
        self.collection.session.add(only_one_group)
        self.collection.session.commit()

        internalLink = db.InternalLinks(cre=dbcre.id, group=dbgroup.id)
        internalLink2 = db.InternalLinks(cre=dbcre.id, group=dbgroup2.id)
        internalLink3 = db.InternalLinks(
            cre=only_one_group.id, group=dbgroup.id)
        self.collection.session.add(internalLink)
        self.collection.session.add(internalLink2)
        self.collection.session.add(internalLink3)
        self.collection.session.commit()

        # happy path, find cre with 2 groups
        groups = self.collection.find_groups_of_cre(dbcre)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups, [dbgroup, dbgroup2])

        # find cre with 1 group
        group = self.collection.find_cres_of_cre(only_one_group)
        self.assertEqual(len(group), 1)
        self.assertEqual(group, [dbgroup])

        # ensure that None is return if there are no groups
        groups = self.collection.find_cres_of_cre(groupless_cre)
        self.assertIsNone(groups)

    def test_find_cres_of_standard(self):
        dbcre = db.CRE(description="CREdesc1", name="CREname1")
        dbgroup = db.CRE(description="CREdesc2", name="CREname2")
        dbstandard1 = db.Standard(section="section1", name="standard1")
        group_standard = db.Standard(section="section2", name="standard2")
        lone_standard = db.Standard(section="section3", name="standard3")

        self.collection.session.add(dbcre)
        self.collection.session.add(dbgroup)
        self.collection.session.add(dbstandard1)
        self.collection.session.add(group_standard)
        self.collection.session.add(lone_standard)
        self.collection.session.commit()

        self.collection.session.add(
            db.Links(cre=dbcre.id, standard=dbstandard1.id))
        self.collection.session.add(
            db.Links(cre=dbgroup.id, standard=dbstandard1.id))
        self.collection.session.add(
            db.Links(cre=dbgroup.id, standard=group_standard.id)
        )
        self.collection.session.commit()

        # happy path, 1 group and 1 cre link to 1 standard
        cres = self.collection.find_cres_of_standard(dbstandard1)
        self.assertEqual(len(cres), 2)
        self.assertEqual(cres, [dbcre, dbgroup])

        # group links to standard
        cres = self.collection.find_cres_of_standard(group_standard)
        self.assertEqual(len(cres), 1)
        self.assertEqual(cres, [dbgroup])

        # no links = None
        cres = self.collection.find_cres_of_standard(lone_standard)
        self.assertIsNone(cres)

    def test_get_CRE(self):
        """Given: a cre 'C1' that links to cres both as a group and a cre and other standards
        return the CRE in Document format"""
        collection = db.Standard_collection()
        dbc1 = db.CRE(external_id="123", description="CD1", name="C1")
        dbc2 = db.CRE(description="CD2", name="C2")
        dbc3 = db.CRE(description="CD3", name="C3")
        dbs1 = db.Standard(name="S2", section="1", subsection="2", link="3")

        collection.session.add(dbc1)
        collection.session.add(dbc2)
        collection.session.add(dbc3)
        collection.session.add(dbs1)
        collection.session.commit()
        collection.session.add(db.InternalLinks(group=dbc1.id, cre=dbc2.id))
        collection.session.add(db.InternalLinks(group=dbc3.id, cre=dbc1.id))
        collection.session.add(db.Links(cre=dbc1.id, standard=dbs1.id))
        collection.session.commit()

        expected = defs.CRE(
            id="123",
            description="CD1",
            name="C1",
            links=[
                defs.Link(
                    document=defs.Standard(
                        name="S2", section="1", subsection="2", hyperlink="3"
                    )
                ),
                defs.Link(document=defs.CRE(description="CD2", name="C2")),
                defs.Link(document=defs.CRE(description="CD3", name="C3")),
            ],
        )

        res = collection.get_CRE(name="C1")
        self.assertEqual(expected, res)

    def test_get_standards(self):
        """Given: a Standard 'S1' that links to cres
        return the Standard in Document format"""
        collection = db.Standard_collection()
        dbc1 = db.CRE(external_id="123", description="CD1", name="C1")
        dbc2 = db.CRE(description="CD2", name="C2")
        dbc3 = db.CRE(description="CD3", name="C3")
        dbs1 = db.Standard(name="S1", section="1", subsection="2", link="3")

        collection.session.add(dbc1)
        collection.session.add(dbc2)
        collection.session.add(dbc3)
        collection.session.add(dbs1)
        collection.session.commit()
        collection.session.add(db.Links(cre=dbc1.id, standard=dbs1.id))
        collection.session.add(db.Links(cre=dbc2.id, standard=dbs1.id))
        collection.session.add(db.Links(cre=dbc3.id, standard=dbs1.id))
        collection.session.commit()

        expected = [
            defs.Standard(
                name="S1",
                section="1",
                subsection="2",
                hyperlink="3",
                links=[
                    defs.Link(
                        document=defs.CRE(
                            name="C1", description="CD1", id="123")
                    ),
                    defs.Link(document=defs.CRE(name="C2", description="CD2")),
                    defs.Link(document=defs.CRE(name="C3", description="CD3")),
                ],
            )
        ]

        res = collection.get_standards(name="S1")
        self.assertEqual(expected, res)

    def test_gap_analysis(self):
        """ Given 
        the following standards SA1, SA2, SA3 SAA1 , SB1, SD1, SDD1, SW1, SX1
        the following CREs CA, CB, CC, CD, CDD , CW, CX
        the following links
        CC -> CA, CB,CD
        CD -> CDD
        CA-> SA1, SAA1
        CB -> SB1
        CD -> SD1
        CDD -> SDD1
        CW -> SW1
        CX -> SA3, SX1
        NoCRE -> SA2

        Then:
        gap_analysis(SA) returns SA1, SA2, SA3
        gap_analysis(SA,SAA) returns SA1 <-> SAA1, SA2, SA3
        gap_analysis(SA,SDD) returns SA1 <-> SDD1, SA2, SA3
        gap_analysis(SA, SW) returns SA1,SA2,SA3, SW1 # no connection
        gap_analysis(SA, SB, SD, SW) returns SA1 <->(SB1,SD1), SA2 , SW1, SA3
        gap_analysis(SA, SX) returns SA1, SA2, SA3->SX1

            give me a single standard
            give me two standards connected by same cre
            give me two standards connected by cres who are children of the same cre
            give me two standards connected by completely different cres
            give me two standards with sections on different trees.

            give me two standards without  connections
            give me 3 or more standards

        """

        collection = db.Standard_collection()
        cres = {"dbca": db.CRE(external_id="1", description="CA", name="CA"),
                'dbcb': db.CRE(external_id="2", description="CB", name="CB"),
                'dbcc': db.CRE(external_id="3", description="CC", name="CC"),
                'dbcd': db.CRE(external_id="4", description="CD", name="CD"),
                'dbcdd': db.CRE(external_id="5", description="CDD", name="CDD"),
                'dbcw': db.CRE(external_id="6", description="CW", name="CW"),
                'dbcx': db.CRE(external_id="7", description="CX", name="CX")
                }
        standards = {'dbsa1': db.Standard(name="SA", section="SA1", subsection="", link=""),
                     'dbsa2': db.Standard(name="SA", section="SA2", subsection="", link=""),
                     'dbsa3': db.Standard(name="SA", section="SA3", subsection="", link=""),
                     'dbsaa1': db.Standard(name="SAA", section="SAA1", subsection="", link=""),
                     'dbsb1': db.Standard(name="SB", section="SB1", subsection="", link=""),
                     'dbsd1': db.Standard(name="SD", section="SD1", subsection="", link=""),
                     'dbsdd1': db.Standard(name="SDD", section="SDD1", subsection="", link=""),
                     'dbsw1': db.Standard(name="SW", section="SW1", subsection="", link=""),
                     'dbsx1': db.Standard(name="SX", section="SX1", subsection="", link="")
                     }

        for cre in cres.values():
            collection.session.add(cre)
        for standard in standards.values():
            collection.session.add(standard)
        collection.session.commit()

        collection.session.add(
            db.Links(cre=cres['dbca'].id, standard=standards['dbsa1'].id))
        collection.session.add(
            db.Links(cre=cres['dbca'].id, standard=standards['dbsaa1'].id))
        collection.session.add(
            db.Links(cre=cres['dbcb'].id, standard=standards['dbsb1'].id))
        collection.session.add(
            db.Links(cre=cres['dbcd'].id, standard=standards['dbsd1'].id))
        collection.session.add(
            db.Links(cre=cres['dbcdd'].id, standard=standards['dbsdd1'].id))
        collection.session.add(
            db.Links(cre=cres['dbcw'].id, standard=standards['dbsw1'].id))
        collection.session.add(
            db.Links(cre=cres['dbcx'].id, standard=standards['dbsa3'].id))
        collection.session.add(
            db.Links(cre=cres['dbcx'].id, standard=standards['dbsx1'].id))

        collection.session.add(db.InternalLinks(
            group=cres['dbcc'].id, cre=cres['dbca'].id))
        collection.session.add(db.InternalLinks(
            group=cres['dbcc'].id, cre=cres['dbcb'].id))
        collection.session.add(db.InternalLinks(
            group=cres['dbcc'].id, cre=cres['dbcd'].id))
        collection.session.add(db.InternalLinks(
            group=cres['dbcd'].id, cre=cres['dbcdd'].id))

        collection.session.commit()

        sa1 = defs.Standard(name="SA", section="SA1")
        sa2 = defs.Standard(name="SA", section="SA2")
        sa3 = defs.Standard(name="SA", section="SA3")
        saa1 = defs.Standard(name="SAA", section="SAA1")
        sdd1 = defs.Standard(name="SDD", section="SDD1")
        sw1 = defs.Standard(name="SW", section="SW1")
        sb1 = defs.Standard(name="SB", section="SB1")
        sd1 = defs.Standard(name="SD", section="SD1")
        sx1 = defs.Standard(name="SX", section="SX1")
        expected = {
            "SA": [sa1, sa2, sa3],
            "SA,SAA": [copy.copy(sa1).add_link(defs.Link(document=saa1)), copy.copy(saa1).add_link(defs.Link(document=sa1)), sa2, sa3],
            "SAA,SA": [copy.copy(sa1).add_link(defs.Link(document=saa1)), copy.copy(saa1).add_link(defs.Link(document=sa1)), sa2, sa3],
            "SA,SDD": [copy.copy(sa1).add_link(defs.Link(document=sdd1)), copy.copy(sdd1).add_link(defs.Link(document=sa1)), sa2, sa3],
            "SA,SW": [sa1, sa2, sa3, sw1],
            "SA,SB,SD,SW": [copy.copy(sa1).add_link(defs.Link(document=sb1)).add_link(defs.Link(document=sd1)),
                            copy.copy(sb1).add_link(defs.Link(document=sa1)).add_link(
                defs.Link(document=sd1)),
                copy.copy(sd1).add_link(defs.Link(document=sa1)).add_link(
                defs.Link(document=sb1)),
                sa2, sa3, sw1],
            "SA,SX": [sa1, sa2, copy.copy(sa3).add_link(defs.Link(document=sx1)),
                      copy.copy(sx1).add_link(defs.Link(document=sa3))],
        }

        self.maxDiff = None
        for args, expected_vals in expected.items():
            stands = args.split(",")
            res = self.collection.gap_analysis(stands)
            # unfortunately named, asserts element and count equality
            self.assertCountEqual(res, expected_vals)


if __name__ == "__main__":
    unittest.main()
