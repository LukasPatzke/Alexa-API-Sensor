# -*- coding: utf-8 -*-

# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in
# compliance with the License. A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import json

import boto3
from botocore.exceptions import ClientError

from endpoint_cloud.api_handler_event import ApiHandlerEvent
from .api_utils import ApiUtils

dynamodb_aws = boto3.client('dynamodb')

DEFAULT_CAPABILITIES = [
    {
        "type": "AlexaInterface",
        "interface": "Alexa.ContactSensor",
        "version": "3",
        "properties": {
            "supported": [
                {
                "name": "detectionState"
                }
            ],
        "proactivelyReported": True,
        "retrievable": True
        }
    },
    {
        "type": "AlexaInterface",
        "interface": "Alexa.EndpointHealth",
        "version": "3",
        "properties": {
            "supported": [
                {
                "name": "connectivity"
                }
            ],
        "proactivelyReported": True,
        "retrievable": True
        }
    }
]


class ApiHandlerEndpoint:
    class EndpointDetails:
        def __init__(self):
            self.capabilities = ''
            self.description = 'Sample Description'
            self.display_categories = ['CONTACT_SENSOR']
            self.friendly_name = ApiUtils.get_random_color_string() + ' Sample Endpoint'
            self.id = 'SAMPLE_ENDPOINT_' + ApiUtils.get_code_string(8)
            self.manufacturer_name = 'Lukas Patzke'
            self.user_id = '0'

        def dump(self):
            print('EndpointDetails -----')
            print('capabilities:', self.capabilities)
            print('description:', self.description)
            print('display_categories:', self.display_categories)
            print('friendly_name:', self.friendly_name)
            print('id:', self.id)
            print('manufacturer_name:', self.manufacturer_name)
            print('user_id:', self.user_id)

    def create(self, request):
        try:
            endpoint_details = self.EndpointDetails()

            # Map our incoming API body to a thing that will virtually represent a discoverable device for Alexa
            json_object = json.loads(request['body'])
            endpoint = json_object['event']['endpoint']
            endpoint_details.user_id = endpoint['userId']  # Expect a Profile
            if 'capabilities' in endpoint:
                endpoint_details.capabilities = endpoint['capabilities']
            else:
                endpoint_details.capabilities = DEFAULT_CAPABILITIES

            if 'friendlyName' in endpoint:
                endpoint_details.friendly_name = endpoint['friendlyName']

            if 'manufacturerName' in endpoint:
                endpoint_details.manufacturer_name = endpoint['manufacturerName']

            if 'description' in endpoint:
                endpoint_details.description = endpoint['description']

            if 'displayCategories' in endpoint:
                endpoint_details.display_categories = endpoint['displayCategories']

            if 'endpointId' in endpoint:
                endpoint_details.id = endpoint['endpointId']
                
            # Create the thing details in DynamoDb
            response = self.create_endpoint_details(endpoint_details)
            if not ApiUtils.check_response(response):
                print('ERR api_handler_endpoint.create.create_thing_details.response', response)

            # Send an Event that updates Alexa
            endpoint = {
                'userId': endpoint_details.user_id,
                'id': endpoint_details.id,
                'friendlyName': endpoint_details.friendly_name,
                'manufacturerName': endpoint_details.manufacturer_name,
                'description': endpoint_details.description,
                'displayCategories': endpoint_details.display_categories,
                'capabilities': endpoint_details.capabilities
            }

            # Package into an Endpoint Cloud Event
            event_request = {'event': {'type': 'AddOrUpdateReport', 'endpoint': endpoint}}
            event_body = {'body': json.dumps(event_request)}
            event = ApiHandlerEvent().create(event_body)
            print(json.dumps(event, indent=2))
            return response

        except KeyError as key_error:
            return "KeyError: " + str(key_error)

            
    @staticmethod
    def create_endpoint_details(endpoint_details):
        print('LOG api_handler_endpoint.create_endpoint_details -----')
        print('LOG api_handler_endpoint.create_endpoint_details.endpoint_details', endpoint_details.dump())
        dynamodb_aws_resource = boto3.resource('dynamodb')
        table = dynamodb_aws_resource.Table('APISensorEndpointDetails')
        print('LOG api_handler_endpoint.create_endpoint_details Updating Item in APISensorEndpointDetails')
        try:
            response = table.update_item(
                Key={
                    'EndpointId': endpoint_details.id
                },
                UpdateExpression='SET \
                        Capabilities = :capabilities, \
                        Description = :description, \
                        DisplayCategories = :display_categories, \
                        FriendlyName = :friendly_name, \
                        ManufacturerName = :manufacturer_name, \
                        UserId = :user_id',
                ExpressionAttributeValues={
                    ':capabilities': str(json.dumps(endpoint_details.capabilities)),
                    ':description': str(endpoint_details.description),
                    ':display_categories': str(json.dumps(endpoint_details.display_categories)),
                    ':friendly_name': str(endpoint_details.friendly_name),
                    ':manufacturer_name': str(endpoint_details.manufacturer_name),
                    ':user_id': str(endpoint_details.user_id)

                }
            )
            print(json.dumps(response))
            return response
        except Exception as e:
            print(e)
            return None

    def delete(self, request):
        try:
            response = {}
            print(request)
            json_object = json.loads(request['body'])
            endpoint_ids = []
            delete_all_endpoints = False
            for endpoint_id in json_object:
                # Special Case for * - If any match, delete all
                if endpoint_id == '*':
                    delete_all_endpoints = True
                    break
                endpoint_ids.append(endpoint_id)

            if delete_all_endpoints is True:
                self.delete_all()
                response = {'message': 'Deleted all endpoints'}

            for endpoint_id in endpoint_ids:
                self.delete_endpoint(endpoint_id)

            return response

        except KeyError as key_error:
            return "KeyError: " + str(key_error)

    def delete_all(self):
        table = boto3.resource('dynamodb').Table('APISensorEndpointDetails')
        result = table.scan()
        items = result['Items']
        for item in items:
            endpoint_id = item['EndpointId']
            self.delete_endpoint(endpoint_id)

    # TODO Improve response handling
    # TODO Check Response
    # TODO UPDATE ALEXA!
    # Send AddOrUpdateReport to Alexa Event Gateway
    @staticmethod
    def delete_endpoint(endpoint_id):

        # Delete from DynamoDB
        response = dynamodb_aws.delete_item(
            TableName='APISensorEndpointDetails',
            Key={'EndpointId': {'S': endpoint_id}}
        )

        # Package into an Endpoint Cloud Event
        event_request = {'event': {'type': 'DeleteReport', 'endpoint': {'id': endpoint_id}}}
        event_body = {'body': json.dumps(event_request)}
        event = ApiHandlerEvent().create(event_body)
        print(json.dumps(event, indent=2))

        print('LOG api_handler_endpoint.delete_endpoint.dynamodb_aws.delete_item.response -----')
        print(response)

        return response

    def read(self, request):
        try:
            response = {}
            resource = request['resource']
            if resource == '/endpoints':

                table = boto3.resource('dynamodb').Table('APISensorEndpointDetails')
                result = table.scan()
                response = result['Items']

            print('LOG api_handler_endpoint.read -----')
            print(json.dumps(response))
            return response

        except KeyError as key_error:
            return "KeyError: " + str(key_error)


    # TODO Work in Progress: Update the Endpoint Details
    @staticmethod
    def update(request):
        raise NotImplementedError()
        # TODO Get the endpoint ID
        # TODO With the endpoint ID, Get the endpoint information from IoT
        # TODO With the endpoint ID, Get the endpoint details from DDB
        #     Get the endpoint as JSON pre-configured
        # TODO Send a command to IoT to update the endpoint
        # TODO Send a command to DDB to update the endpoint
        # TODO UPDATE ALEXA!
        # Send AddOrUpdateReport to Alexa Event Gateway

    # TODO Work in Progress: Update Endpoint States
    @staticmethod
    def update_states(request, states):
        raise NotImplementedError()
        # TODO Get the endpoint ID
        # TODO With the endpoint ID, Get the endpoint information from IoT
        # TODO With the endpoint ID, Get the endpoint details from DDB
        #     Get the endpoint as JSON pre-configured
        # TODO Send a command to IoT to update the endpoint
        # TODO Send a command to DDB to update the endpoint
        # TODO UPDATE ALEXA!
        # Send ChangeReport to Alexa Event Gateway

