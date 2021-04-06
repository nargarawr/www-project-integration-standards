import json
import db
from flask import Flask, jsonify, Blueprint
from flask import request
from pprint import pprint
app = Flask(__name__)

cache_loc = 'standards_cache.sqlite'
database = db.Standard_collection(cache=True, cache_file=cache_loc)

# cre = Blueprint('cres', __name__)
# app.register_blueprint(cre, url_prefix='/cre')

@app.route('/id/<creid>', methods=["GET"])
def find_by_id(creid): # refer
    cre = database.get_CRE(id=creid)
    if cre:
        pprint(cre.todict())
        return jsonify(cre.todict())

@app.route('/name/<crename>', methods=["GET"])
def find_by_name(crename):
    cre = database.get_CRE(name=crename)
    if cre:
        pprint(cre.todict())
        return jsonify(cre.todict())

@app.route('/standard/<sname>', methods=["GET"])
def find_standard_by_name(sname):
    opt_section = request.args.get('section')
    opt_subsection = request.args.get('subsection')
    opt_hyperlink = request.args.get('hyperlink')

    standards = database.get_standard(name=sname,section=opt_section,subsection=opt_subsection, link = opt_hyperlink)
    if standards:
        res = [stand.todict() for stand in standards]
        return jsonify(res)


app.run()