import os
import redis

from flask import Flask
from flask import request, redirect, render_template, url_for
from flask import Response

# Datadog tracing and metrics
from datadog import initialize, statsd
from ddtrace import tracer, patch_all

# If we're getting a DogStatD host (i.e. running in Kubernetes), initialize with it.
if "DOGSTATSD_HOST_IP" in os.environ:
  initialize(statsd_host = os.environ.get("DOGSTATSD_HOST_IP"))
  tracer.configure(hostname = os.environ.get("DOGSTATSD_HOST_IP"))

# Apply some base tags and patch for Datadog tracing.
patch_all()

redishost = 'redis-master'
if 'REDIS_HOST' in os.environ:
    redishost = os.environ.get('REDIS_HOST')

app = Flask(__name__)
app.redis = redis.StrictRedis(host=redishost, port=6379, db=0)

# Be super aggressive about saving for the development environment.
# This says save every second if there is at least 1 change.  If you use
# redis in production you'll want to read up on the redis persistence
# model.
app.redis.config_set('save', '1 1')

@app.route('/', methods=['GET', 'POST'])
def main_page():
    if request.method == 'POST':
        statsd.increment("guestbook.post")
        app.redis.lpush('entries', request.form['entry'])
        return redirect(url_for('main_page'))
    else:
        statsd.increment("guestbook.view")
        entries = app.redis.lrange('entries', 0, -1)
        return render_template('main.html', entries=entries)

@app.route('/clear', methods=['POST'])
def clear_entries():
    statsd.increment("guestbook.clear")
    app.redis.ltrim('entries', 1, 0)
    return redirect(url_for('main_page'))

if __name__ == "__main__":
  app.run(host='0.0.0.0', port=5000)
