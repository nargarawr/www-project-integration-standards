import os
import unittest
from application import sqla, create_app
import sys
import click

app = create_app(mode=os.getenv('FLASK_CONFIG') or 'default')
sqla.create_all(app=app)

# @app.shell_context_processor
# def make_shell_context():
#     return dict(db=sqla)


@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')
@click.argument('test_names', nargs=-1)
def test(coverage, test_names):
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))

    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        # tests = unittest.TestLoader().run('application/tests/dummy_test.py')
        tests = unittest.TestLoader().discover("application/tests",pattern="*_test.py")
    unittest.TextTestRunner(verbosity=2).run(tests)