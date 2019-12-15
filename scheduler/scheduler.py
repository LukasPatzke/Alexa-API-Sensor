from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask import Flask
from flask_apscheduler import APScheduler
import requests
import json

class Config(object):

    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }

    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 20}
    }

    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3,
        'func': 'scheduler:trigger_event'
    }

    SCHEDULER_API_ENABLED = True

    SCHEDULER_API_PREFIX = '/api'



def trigger_event(endpoint):

    url = 'http://alexa.pi.lan/api/events'

    body = {
        'event': {
            'type': 'ChangeReport',
            'endpoint': {
                'id': endpoint,
                'state': 'detectionState',
                'value': 'DETECTED',
                'namespace': 'Alexa.ContactSensor'
            }
        }
    }

    response = requests.post(url, data=json.dumps(body))
    print(json.dumps(response.json()))

app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)

if __name__ == '__main__':
    scheduler.start()
    app.run(host='0.0.0.0', port=9090)
