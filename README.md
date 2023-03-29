# TemporalLoop

TemporalLoop is an open-source project that helps you run and manage [Temporal.io](https://temporal.io) workers. It Inspired from how uvicorn works for ASGI applications.
With a simple configuration, you can define multiple workers with their own activities, workflows, queue and settings. 
It aims to reduce boilerplate code, improve worker management, and increase interoperability between Temporal-based projects.

## Features

- Easy configuration with YAML or JSON
- Unify and Simplified worker maintenance across all Temporal's python microservices
- Customizable logging
- Support for DataConverter and Interceptor classes
- Customizable Worker instance
- Launch multiple workers on a single process
- Signal handling (SIGINT, SIGTERM) with graceful shutdown

## Prerequisites

- Python 3.10+
- Temporal.io server (self-hosted or cloud)

## Installation
Install TemporalLoop using pip:

```bash
pip install temporalloop

```

## Configuration
Here's a sample config.yaml for configuring TemporalLoop:


``` yaml
temporalio:
  host: "127.0.0.1:7233"
  namespace: "default"

logging:
  level: "info"
  use_colors: true
  log_config: "path/to/your/log_config.ini"

workers:
  - name: "worker1"
    queue: "first-queue"
    workflows:
      - "your_package.workflows:YourWorkflow"
    activities:
      - "your_package.activities:your_activity_one"
      - "your_package.activities:your_activity_two"

  - name: "worker2"
    queue: "another-queue"
    workflows:
      - "your_package.workflows:YourWorkflow"
    activities:
      - "your_package.activities:your_activity_one"
      
    # Settings can be overrided per worker
    namespace: "staging" 
    interceptors: []  # Skip interceptors for this worker
    factory: "your_package.worker:WorkerFactory"
    
interceptors:
  - "temporalloop.interceptors.sentry:SentryInterceptor"

```


This sample configuration file includes:

- Temporal settings, including the host and namespace
- Logging settings, such as the log level, color usage, and an optional log configuration file
- A list of workers, each with a unique name, task queue, and associated workflows and activities, namespace
- A list of interceptors to be used across all workers 

Replace your_package with your actual package name and provide the appropriate paths for your workflows, activities, and interceptors.

## Usage
### Starting a Worker
You can start a worker either by writing a script or using the command-line interface.
#### Command-Line Example

``` shell
tempoloop --config=config.yaml --host=localhost:7233 --log-level=debug
```

#### Script Example

``` python
# worker.py
from temporalloop.config import Config, WorkerConfig
from temporalloop.main import run

from your_package.workflows import YourWorkflow
from your_package.activities import your_activity_one, your_activity_two

if __name__ == "__main__":
    run(Config(
        host="localhost:7233",
        workers=[
            WorkerConfig(name="worker1",
                         queue="your-queue",
                         workflows=[YourWorkflow],
                         activities=[your_activity_one, your_activity_two],
                         ),
            WorkerConfig(name="worker2",
                         queue="another-queue",
                         workflows=[YourWorkflow],
                         activities=[your_activity_one, your_activity_two],
                         ),
        ],        
    ))
```

Run the script with
``` shell
python worker.py
```


