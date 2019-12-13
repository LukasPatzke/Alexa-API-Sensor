import requests
import os
import json

class SkillClient():
    def __init__(self):
        api_key = os.environ.get('API_KEY', None)

        if api_key is None:
            raise EnvironmentError('API_KEY not found.')
        
        self.base_url = 'https://r1u5u9j6bl.execute-api.eu-west-1.amazonaws.com/prod'
        self.session = requests.Session()
        self.session.headers = {'Content-Type': 'application/json', 'x-api-key': api_key}
        

    def create_endpoint(self, name, endpoint_id=None, description=None, 
            manufacturer_name=None, display_categories=None, capabilities=None):

        url = self.base_url + '/endpoints'

        endpoint = {
            'friendlyName': name,
            'userId': 'amzn1.account.AHGRSDVG3AWD5GUJYMQQWCLC3JJQ'
        }

        if endpoint_id is not None:
            endpoint['endpointId'] = endpoint_id
        if description is not None:
            endpoint['description'] = description
        if manufacturer_name is not None:
            endpoint['manufacturerName'] = manufacturer_name
        if display_categories is not None:
            endpoint['displayCategories'] = display_categories
        if capabilities is not None:
            endpoint['capabilities'] = capabilities

        body = {
            'event': {
                'endpoint': endpoint
            }
        }
        return self.session.post(url, data=json.dumps(body))

    def update_endpoint(self, endpoint_id, name=None, description=None):
        url = self.base_url + '/endpoints'

        endpoint = {
            'endpointId': endpoint_id,
            'userId': 'amzn1.account.AHGRSDVG3AWD5GUJYMQQWCLC3JJQ'
        }

        if name is not None:
            endpoint['friendlyName'] = name
        if description is not None:
            endpoint['description'] = description

        body = {
            'event': {
                'endpoint': endpoint
            }
        }
        return self.session.put(url, data=json.dumps(body))
        
    def send_event(self, endpoint_id):
        url = self.base_url + '/events'

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

        return self.session.post(url, data=json.dumps(body))

    def delete_endpoint(self, endpoint_id):
        url = self.base_url + '/endpoints'

        if isinstance(endpoint_id, list):
            body = endpoint_id
        else:
            body = [endpoint_id]

        return self.session.delete(url, data=json.dumps(body))

    def delete_all(self):
        url = self.base_url + '/endpoints'
        body = ['*']

        return self.session.delete(url, data=json.dumps(body))

    def get_endpoints(self):
        url = self.base_url + '/endpoints'
        return self.session.get(url)

