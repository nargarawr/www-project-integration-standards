
import unittest
import cre_defs as defs
from parsers import *
from pprint import pprint
import collections

class TestParsers(unittest.TestCase):

    def test_parse_uknown_key_val_spreadsheet(self):
        # OrderedDict only necessary for testing  so we can predict the root Standard, normally it wouldn't matter
        input = [collections.OrderedDict({'CS': 'Session Management', 'CWE': 598,
                  'ASVS': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING',
                  'OPC': '',
                  'Top10': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                  'WSTG': 'WSTG-SESS-04'}),
                 collections.OrderedDict({'CS': 'Session Management', 'CWE': 384,
                  'ASVS': 'SESSION-MGT-TOKEN-DIRECTIVES-GENERATION',
                  'OPC': 'C6',
                  'Top10': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                  'WSTG': 'WSTG-SESS-03'})]
        expected = {'CS-Session Management': defs.Standard(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard, id='', description='',
                                                           name='CS', links=[defs.Standard(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard, id='', description='', name='CWE', links=[], tags=[], metadata=defs.Metadata(labels=[]), section='598'),
                                                                            defs.Standard(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard, id='', description='', name='ASVS', links=[], tags=[], metadata=defs.Metadata(labels=[]), section='SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING'),
                                                                            defs.Standard(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard, id='', description='', name='Top10', links=[], tags=[], metadata=defs.Metadata(labels=[]), section='https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control'),
                                                                            defs.Standard(version=defs.CreVersions.V2, doctype=defs.Credoctypes.Standard, id='', description='', name='WSTG', links=[], tags=[], metadata=defs.Metadata(labels=[]), section='WSTG-SESS-04')
                                                                            ], tags=[], metadata=defs.Metadata(labels=[]), section='Session Management')}
        self.maxDiff = None
        actual = parse_uknown_key_val_spreadsheet(input)
        for key,val in actual.items():
            self.assertEqual(expected[key],val)

    def test_parse_v0_standards(self):
        input = [{'CRE-ID-lookup-from-taxonomy-table': '011-040-026', 'CS': 'Session Management', 'CWE': 598,
                  'Description': 'Verify the application never reveals session tokens in URL parameters or error messages.',
                  'Development guide (does not exist for SessionManagement)': '',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING',
                  'Item': '3.1.1', 'Name': 'Session', 'OPC': '',
                  'Top10 (lookup)': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                  'WSTG': 'WSTG-SESS-04'},
                 {'CRE-ID-lookup-from-taxonomy-table': '011-040-033', 'CS': 'Session Management', 'CWE': 384,
                  'Description': 'Verify the application generates a new session token on user '
                  'authentication.', 'Development guide (does not exist for SessionManagement)': '',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SESSION-MGT-TOKEN-DIRECTIVES-GENERATION',
                  'Item': '3.2.1', 'Name': 'Session', 'OPC': 'C6',
                  'Top10 (lookup)': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                  'WSTG': 'WSTG-SESS-03'}]
        expected = {'011-040-026': defs.CRE(version=defs.CreVersions.V0, doctype=defs.Credoctypes.CRE, name='011-040-026',
                                            description='Verify the application never reveals session tokens in URL parameters or error messages.',
                                            links=[
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='ASVS',
                                                              section='SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING', subsection='3.1.1'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='CS',
                                                              section='Session Management'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='CWE',
                                                              section='598'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='Name',
                                                              section='Session'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='Top10 (lookup)',
                                                              section='https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='WSTG', section='WSTG-SESS-04')]),
                    '011-040-033': defs.CRE(version=defs.CreVersions.V0, doctype=defs.Credoctypes.CRE,   name='011-040-033',
                                            description='Verify the application generates a new session token on user authentication.',
                                            links=[
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard,   name='ASVS',
                                                              section='SESSION-MGT-TOKEN-DIRECTIVES-GENERATION', subsection='3.2.1'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='CS',
                                                              section='Session Management'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='CWE',
                                                              section='384'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='Name',
                                                              section='Session'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='OPC',
                                                              section='C6'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='Top10 (lookup)',
                                                              section='https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control'),
                                                defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='WSTG',
                                                              section='WSTG-SESS-03')])}
        self.maxDiff = None
        output = parse_v0_standards(input)
        for key, value in output.items():
            self.assertEqual(expected[key], value)

    def test_parse_v1_standards(self):
        input = [{'ASVS Item': 'V1.1.1', 'ASVS-L1': '', 'ASVS-L2': 'X', 'ASVS-L3': 'X', 'CORE-CRE-ID': '002-036',
                  'CRE Group 1': 'SDLC_GUIDELINES_JUSTIFICATION', 'CRE Group 1 Lookup': '925-827',
                  'CRE Group 2': 'REQUIREMENTS', 'CRE Group 2 Lookup': '654-390',
                  'CRE Group 3': 'RISK_ANALYSIS', 'CRE Group 3 Lookup': '533-658',
                  'CRE Group 4': 'THREAT_MODEL', 'CRE Group 4 Lookup': '635-846',
                  'CRE Group 5': '', 'CRE Group 5 Lookup': '',
                  'CRE Group 6': '', 'CRE Group 6 Lookup': '',
                  'CRE Group 7': '', 'CRE Group 7 Lookup': '',
                  'CWE': 0, 'Cheat Sheet': 'Architecture, Design and Threat Modeling Requirements',
                  'Core-CRE (high-level description/summary)': 'SDLC_APPLY_CONSISTENTLY',
                  'Description': 'Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL',
                  'NIST 800-53 - IS RELATED TO': 'RA-3 RISK ASSESSMENT,\n'
                                 'PL-8 SECURITY AND PRIVACY ARCHITECTURES',
                  'NIST 800-63': 'None', 'OPC': 'C1', 'SIG ISO 25010': '@SDLC', 'Top10 2017': '', 'WSTG': '',
                  'cheat_sheets': 'https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html'}]

        expected = ({'REQUIREMENTS': defs.CreGroup(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Group, id='654-390', description='', name='REQUIREMENTS',
                                                   links=[
                                                       defs.CRE(version=defs.CreVersions.V1, doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                links=[
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='ASVS', links=[], tags=[
                                                                        'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='CWE', links=[
                                                                    ], tags=[], section='0'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='Cheatsheet', links=[], tags=[], section='Architecture, Design and Threat Modeling Requirements',
                                                                                  hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                    ], tags='is related to', section='RA-3 RISK ASSESSMENT,'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                    ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='OPC', links=[
                                                                    ], tags=[], section='C1'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='SIG ISO 25010', links=[], tags=[], section='@SDLC')],
                                                                tags=[])], tags=[]),
                     'RISK_ANALYSIS': defs.CreGroup(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Group, id='533-658', description='', name='RISK_ANALYSIS',
                                                    links=[
                                                        defs.CRE(version=defs.CreVersions.V1, doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                 links=[
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='ASVS', links=[], tags=[
                                                                                   'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL'),
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='CWE', links=[
                                                                     ], tags=[], section='0'),
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='Cheatsheet', links=[], tags=[], section='Architecture, Design and Threat Modeling Requirements',
                                                                                   hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html'),
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                     ], tags='is related to', section='RA-3 RISK ASSESSMENT,'),
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                     ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES'),
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='OPC', links=[
                                                                     ], tags=[], section='C1'),
                                                                     defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='SIG ISO 25010', links=[], tags=[], section='@SDLC')],
                                                                 tags=[])], tags=[]),
                    'SDLC_GUIDELINES_JUSTIFICATION': defs.CreGroup(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Group, id='925-827', description='', name='SDLC_GUIDELINES_JUSTIFICATION',
                                                                   links=[
                                                                       defs.CRE(version=defs.CreVersions.V1, doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                                links=[
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='ASVS', links=[], tags=[
                                                                                        'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL'),
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='CWE', links=[
                                                                                    ], tags=[], section='0'),
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='Cheatsheet', links=[], tags=[], section='Architecture, Design and Threat Modeling Requirements',
                                                                                                  hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html'),
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                                    ], tags='is related to', section='RA-3 RISK ASSESSMENT,'),
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                                    ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES'),
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='OPC', links=[
                                                                                    ], tags=[], section='C1'),
                                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='SIG ISO 25010', links=[], tags=[], section='@SDLC')],
                                                                                tags=[])], tags=[]),
                     'THREAT_MODEL': defs.CreGroup(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Group, id='635-846', description='', name='THREAT_MODEL',
                                                   links=[
                                                       defs.CRE(version=defs.CreVersions.V1, doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                links=[
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='ASVS', links=[], tags=[
                                                                        'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard,
                                                                                  id='', description='', name='CWE', links=[], tags=[], section='0'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='Cheatsheet', links=[], tags=[], section='Architecture, Design and Threat Modeling Requirements',
                                                                                  hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='',
                                                                                  name='NIST 800-53', links=[], tags='is related to', section='RA-3 RISK ASSESSMENT,'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='NIST 800-53', links=[
                                                                    ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard,
                                                                                  id='', description='', name='OPC', links=[], tags=[], section='C1'),
                                                                    defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, id='', description='', name='SIG ISO 25010', links=[], tags=[], section='@SDLC')],
                                                                tags=[])], tags=[])}, {})

        self.maxDiff = None
        output = parse_v1_standards(input)

        for key, value in output[0].items():
            self.assertEqual(expected[0][key], value)
        for key, value in output[1].items():
            self.assertEqual(expected[1][key], value)


if __name__ == '__main__':
    unittest.main()
