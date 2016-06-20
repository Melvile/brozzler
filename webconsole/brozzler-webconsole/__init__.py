#
# brozzler-webconsole/__init__.py - flask app for brozzler web console, defines
# api endspoints etc
#
# Copyright (C) 2014-2016 Internet Archive
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import flask
import rethinkstuff
import json
import sys
import os
import importlib
import rethinkdb

# XXX flask does its own logging config
# import logging
# logging.basicConfig(stream=sys.stdout, level=logging.INFO,
#         format="%(asctime)s %(process)d %(levelname)s %(threadName)s %(name)s.%(funcName)s(%(filename)s:%(lineno)d) %(message)s")

app = flask.Flask(__name__)

# configure with environment variables
SETTINGS = {
    'RETHINKDB_SERVERS': os.environ.get(
        'RETHINKDB_SERVERS', 'localhost').split(','),
    'RETHINKDB_DB': os.environ.get('RETHINKDB_DB', 'brozzler'),
    'WAYBACK_BASEURL': os.environ.get(
        'WAYBACK_BASEURL', 'http://wbgrp-svc107.us.archive.org:8091'),
}
r = rethinkstuff.Rethinker(
        SETTINGS['RETHINKDB_SERVERS'], db=SETTINGS['RETHINKDB_DB'])
service_registry = rethinkstuff.ServiceRegistry(r)

@app.route("/api/sites/<site_id>/queued_count")
@app.route("/api/site/<site_id>/queued_count")
def queued_count(site_id):
    count = r.table("pages").between(
            [site_id, 0, False, r.minval], [site_id, 0, False, r.maxval],
            index="priority_by_site").count().run()
    return flask.jsonify(count=count)

@app.route("/api/sites/<site_id>/queue")
@app.route("/api/site/<site_id>/queue")
def queue(site_id):
    app.logger.info("flask.request.args=%s", flask.request.args)
    start = flask.request.args.get("start", 0)
    end = flask.request.args.get("end", start + 90)
    queue_ = r.table("pages").between(
            [site_id, 0, False, r.minval], [site_id, 0, False, r.maxval],
            index="priority_by_site")[start:end].run()
    return flask.jsonify(queue_=list(queue_))

@app.route("/api/sites/<site_id>/pages_count")
@app.route("/api/site/<site_id>/pages_count")
@app.route("/api/sites/<site_id>/page_count")
@app.route("/api/site/<site_id>/page_count")
def page_count(site_id):
    count = r.table("pages").between(
            [site_id, 1, False, r.minval],
            [site_id, r.maxval, False, r.maxval],
            index="priority_by_site").count().run()
    return flask.jsonify(count=count)

@app.route("/api/sites/<site_id>/pages")
@app.route("/api/site/<site_id>/pages")
def pages(site_id):
    """Pages already crawled."""
    app.logger.info("flask.request.args=%s", flask.request.args)
    start = int(flask.request.args.get("start", 0))
    end = int(flask.request.args.get("end", start + 90))
    pages_ = r.table("pages").between(
            [site_id, 1, False, r.minval],
            [site_id, r.maxval, False, r.maxval],
            index="priority_by_site")[start:end].run()
    return flask.jsonify(pages=list(pages_))

@app.route("/api/sites/<site_id>")
@app.route("/api/site/<site_id>")
def site(site_id):
    site_ = r.table("sites").get(site_id).run()
    return flask.jsonify(site_)

@app.route("/api/stats/<bucket>")
def stats(bucket):
    stats_ = r.table("stats").get(bucket).run()
    return flask.jsonify(stats_)

@app.route("/api/jobs/<int:job_id>/sites")
@app.route("/api/job/<int:job_id>/sites")
def sites(job_id):
    sites_ = r.table("sites").get_all(job_id, index="job_id").run()
    return flask.jsonify(sites=list(sites_))

@app.route("/api/jobs/<int:job_id>")
@app.route("/api/job/<int:job_id>")
def job(job_id):
    job_ = r.table("jobs").get(job_id).run()
    return flask.jsonify(job_)

@app.route("/api/workers")
def workers():
    workers_ = service_registry.available_services("brozzler-worker")
    return flask.jsonify(workers=list(workers_))

@app.route("/api/services")
def services():
    services_ = service_registry.available_services()
    return flask.jsonify(services=list(services_))

@app.route("/api/jobs")
def jobs():
    jobs_ = list(r.table("jobs").order_by(rethinkdb.desc("id")).run())
    return flask.jsonify(jobs=jobs_)

@app.route("/api/config")
def config():
    return flask.jsonify(config=SETTINGS)

@app.route("/api/<path:path>")
@app.route("/api", defaults={"path":""})
def api404(path):
    flask.abort(404)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def root(path):
    return flask.render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)

