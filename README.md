# Example Guestbook Application

This repo contains an example guestbook to demonstrate how to instrument a basic application.

## The TL;DR

This application is intended to be run on Kubernetes. Note that all YAML files are complete and contain the necessary service, deployment, and RBAC definitions.

To run the application:

```
# All YAML is in the kubernetes directory
cd kubernetes

# Start the Redis master and slave
kubectl apply -f redis-master.yaml
kubectl apply -f redis-slave.yaml

# Create a copy of the Datadog Agent YAML
cp datadog-agent.yaml my-datadog-agent.yaml

# IMPORTANT: replace the <YOUR API KEY> placeholder
# in the my-datadog-agent.yaml file with your own
# API key from https://app.datadoghq.com/account/settings#api

# Deploy the Datadog Agent as a DaemonSet
kubectl apply -f my-datadog-agent.yaml

# Create a copy of the Datadog Agent YAML
cp gremlin.yaml my-gremlin.yaml

# IMPORTANT: replace the <YOUR TEAM ID> and <YOUR SECRET KEY>
# placeholders in the my-gremlin.yaml file with your own
# values from https://app.gremlin.com/settings/team

# Deploy Gremlin as a DaemonSet
kubectl apply -f my-gremlin.yaml

# Start the Guestbook
kubectl apply -f guestbook-datadog.yaml
```

Note: Always keep your secret keys safe and never check them into Git! We recommend copying the Datadog and Gremlin YAML files prior to setting your secrets. YAML files prefixed with `my-` will be ignored by Git.

## What's going on?

### The standard application

In the `app` directory you'll find two versions of the guestbook application: `app.py` and `app-datadog.py`.

The `app.py` file contains the un-instrumented version of the application. This application is based on [Flask](http://flask.pocoo.org/), a popular Python application framework. The application has three main responses:

- If the `/` route is requested and a POST message is sent, it will save the message to redis, then return the main guestbook page.
- If the `/` route is requested without a message, the guestbook entries are queried and the main guestbook page is returned.
- If the `/clear` route is requested, the saved messages are deleted and the main guestbook page is returned.

### Adding instrumentation

The `app-datadog.py` version of the application contains a few additions. It imports portions of the `datadog` and `ddtrace` libraries, which provide DogStatsD and Datadog APM support respectively:

```
# Datadog tracing and metrics
from datadog import initialize, statsd
from ddtrace import tracer, patch_all
```

Next, it sets the location of the Datadog Agent. This is required because we will be running in a Kubernetes-based environment. By default, the `datadog` and `ddtrace` libraries will send metrics and traces to `localhost`. While this works well for applications running on servers where the Datadog Agent is installed, for a containerized environment, we need to specify where the Datadog Agent is running. To do this, we're using an environment variable, `DOGSTATSD_HOST_IP`.

```
# If we're getting a DogStatD host (i.e. running in Kubernetes), initialize with it.
if "DOGSTATSD_HOST_IP" in os.environ:
  initialize(statsd_host = os.environ.get("DOGSTATSD_HOST_IP"))
  tracer.configure(hostname = os.environ.get("DOGSTATSD_HOST_IP"))
```

The `DOGSTATSD_HOST_IP` environment variable is set in the `kubernetes/guestbook-datadog.yaml` file under the guestbook's deployment. Here we make use of Kubernetes's [Downward API](https://kubernetes.io/docs/tasks/inject-data-application/environment-variable-expose-pod-information/). Note that this is the only difference between the standard `guestbook.yaml` and the instrumented `guestbook-datadog.yaml`.

```
spec:
  template:
    spec:
      containers:
        ...
        env:
        - name: DOGSTATSD_HOST_IP
          valueFrom:
            fieldRef:
              fieldPath: status.hostIP
```

Next we use the patching feature of the `ddtrace` library. This will automatically instrument the application for Datadog APM.

```
# Apply some base tags and patch for Datadog tracing.
patch_all()
```

Finally, we add some basic counters to track the number of times the application saves new messages, displays the guestbook, and clears the messages. These counters appear as a call to the statsd.increment method and pass a metric name that we can later find and graph in Datadog.

```
statsd.increment("guestbook.post")
```

### Running the Datadog Agent

The Datadog Agent runs as a [Kubernetes Daemonset](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/). This guarantees that one Datadog Agent pod will be running on each node in the Kubernetes cluster. As we saw earlier, each instance of the guestbook application will receive this host node IP using the `DOGSTATSD_HOST_IP` environment variable.

The `datadog-agent.yaml` file also includes an implementation of Kube State Metrics. This allows the Datadog agent to gather more information about the health and performance of the Kubernetes cluster.


### Running Gremlin
TODO: Add info about the Gremlin DS here.
