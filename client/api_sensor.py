import requests
import os
import json

api_key = os.environ.get('API_KEY', None)

if api_key is None:
    raise EnvironmentError('API_KEY not found.')

headers = {'Content-Type': 'application/json', 'x-api-key': api_key}

def create_endpoint(name):

    url = 'https://r1u5u9j6bl.execute-api.eu-west-1.amazonaws.com/prod/endpoints'

    body = {
        'event': {
            'endpoint': {
                'userId': 'amzn1.account.AHGRSDVG3AWD5GUJYMQQWCLC3JJQ',
                'friendlyName': 'Test API Sensor 1'
            }
        }
    }

    r = requests.post(url, data=json.dumps(body), headers=headers)
    print(r.status_code)
    print(json.dumps(r.json()))

def send_event(endpoint_id):

    url = 'https://r1u5u9j6bl.execute-api.eu-west-1.amazonaws.com/prod/events'

    body = {
        'event': {
            'type': 'ChangeReport',
            'endpoint': {
                'userId': 'amzn1.account.AHGRSDVG3AWD5GUJYMQQWCLC3JJQ',
                'id': endpoint_id,
                'state': 'detectionState',
                'value': 'DETECTED',
                'namespace': 'Alexa.ContactSensor'
            }
        }
    }

    r = requests.post(url, data=json.dumps(body), headers=headers)
    print(r.status_code)
    print(json.dumps(r.json()))


def delete_all():

    url = 'https://r1u5u9j6bl.execute-api.eu-west-1.amazonaws.com/prod/endpoints'

    body = ['*']

    r = requests.delete(url, data=json.dumps(body), headers=headers)
    print(r.status_code)
    print(json.dumps(r.json()))

if __name__ == '__main__':
    send_event('SAMPLE_ENDPOINT_SRCTHVP3')
    #delete_all()

    #create_endpoint('Test 2 Sensor')
