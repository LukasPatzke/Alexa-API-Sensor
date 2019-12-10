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
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from alexa.skills.smarthome import AlexaResponse
from jsonschema import validate, SchemaError, ValidationError
from .api_auth import ApiAuth
from .api_handler_endpoint import ApiHandlerEndpoint

dynamodb_aws = boto3.client('dynamodb')

DEFAULT_VAL = {
    'Alexa.ContactSensor': 'NOT_DETECTED',
    'Alexa.EndpointHealth': 'OK'
}

class ApiHandlerDirective:

    @staticmethod
    def get_db_value(value):
        if 'S' in value:
            value = value['S']
        return value

    def process(self, request, client_id, client_secret):
        print('LOG api_handler_directive.process -----')
        # print(json.dumps(request))

        response = None
        # Process an Alexa directive and route to the right namespace
        # Only process if there is an actual body to process otherwise return an ErrorResponse
        json_body = request['body']
        if json_body:
            json_object = json.loads(json_body)
            namespace = json_object['directive']['header']['namespace']

            if namespace == "Alexa":
                name = json_object['directive']['header']['name']
                correlation_token = json_object['directive']['header']['correlationToken']
                token = json_object['directive']['endpoint']['scope']['token']
                endpoint_id = json_object['directive']['endpoint']['endpointId']

                if name == 'ReportState':
                    # Get the User ID from the access_token
                    response_user_id = json.loads(ApiAuth.get_user_id(token).read().decode('utf-8'))
                    result = dynamodb_aws.get_item(TableName='APISensorEndpointDetails', Key={'EndpointId': {'S': endpoint_id}})
                    capabilities_string = self.get_db_value(result['Item']['Capabilities'])
                    capabilities = json.loads(capabilities_string)
                    props=[]
                    for c in capabilities:
                        if not 'properties' in c:
                            continue
                        retrievable = c['properties'].get('retrievable', False)
                        if retrievable:
                            props.append(c)
                        
                    
                    print('Sending StateReport for', response_user_id, 'on endpoint', endpoint_id)
                    statereport_response = AlexaResponse(
                        name='StateReport', 
                        endpoint_id=endpoint_id, 
                        correlation_token=correlation_token, 
                        token=token)
                    
                    for p in props:
                        statereport_response.add_context_property(
                            namespace=p['interface'],
                            name=p['properties']['supported'][0]['name'], 
                            value=DEFAULT_VAL[p['interface']])

                    response = statereport_response.get()

            if namespace == "Alexa.Authorization":
                grant_code = json_object['directive']['payload']['grant']['code']
                grantee_token = json_object['directive']['payload']['grantee']['token']

                # Spot the default from the Alexa.Discovery sample. Use as a default for development.
                if grantee_token == 'access-token-from-skill':
                    user_id = "0"  # <- Useful for development
                    response_object = {
                        'access_token': 'INVALID',
                        'refresh_token': 'INVALID',
                        'token_type': 'Bearer',
                        'expires_in': 9000
                    }
                else:
                    # Get the User ID
                    response_user_id = json.loads(ApiAuth.get_user_id(grantee_token).read().decode('utf-8'))
                    if 'error' in response_user_id:
                        print('ERROR api_handler_directive.process.authorization.user_id:', response_user_id['error_description'])
                        return AlexaResponse(name='ErrorResponse', payload={'type': 'INTERNAL_ERROR', 'message': response_user_id})

                    user_id = response_user_id['user_id']
                    print('LOG api_handler_directive.process.authorization.user_id:', user_id)

                # Get the Access and Refresh Tokens
                api_auth = ApiAuth()
                print('grant_code', grant_code, 'client_id', client_id, 'client_secret', client_secret)
                response_token = api_auth.get_access_token(grant_code, client_id, client_secret)
                response_token_string = response_token.read().decode('utf-8')
                print('LOG api_handler_directive.process.authorization.response_token_string:', response_token_string)
                response_object = json.loads(response_token_string)

                if 'error' in response_object:
                    return AlexaResponse(name='ErrorResponse', payload={'type': 'INTERNAL_ERROR', 'response_object': response_object})

                # Store the retrieved from the Authorization Server
                access_token = response_object['access_token']
                refresh_token = response_object['refresh_token']
                token_type = response_object['token_type']
                expires_in = response_object['expires_in']

                # Calculate expiration
                expiration_utc = datetime.utcnow() + timedelta(seconds=(int(expires_in) - 5))

                # Store the User Information - This is useful for inspection during development
                table = boto3.resource('dynamodb').Table('APISensorUsers')
                result = table.put_item(
                    Item={
                        'UserId': user_id,
                        'GrantCode': grant_code,
                        'GranteeToken': grantee_token,
                        'AccessToken': access_token,
                        'ClientId': client_id,
                        'ClientSecret': client_secret,
                        'ExpirationUTC': expiration_utc.strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                        'RefreshToken': refresh_token,
                        'TokenType': token_type
                    }
                )

                if result['ResponseMetadata']['HTTPStatusCode'] == 200:
                    print('LOG api_handler_directive.process.authorization.SampleUsers.put_item:', result)
                    alexa_accept_grant_response = AlexaResponse(namespace='Alexa.Authorization', name='AcceptGrant.Response')
                    response = alexa_accept_grant_response.get()
                else:
                    error_message = 'Error creating User'
                    print('ERR api_handler_directive.process.authorization', error_message)
                    alexa_error_response = AlexaResponse(name='ErrorResponse')
                    alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': error_message})
                    response = alexa_error_response.get()

            if namespace == "Alexa.Discovery":
                # Given the Access Token, get the User ID
                access_token = json_object['directive']['payload']['scope']['token']

                # Spot the default from the Alexa.Discovery sample. Use as a default for development.
                if access_token == 'access-token-from-skill':
                    print('WARN api_handler_directive.process.discovery.user_id: Using development user_id of 0')
                    user_id = "0"  # <- Useful for development
                else:
                    response_user_id = json.loads(ApiAuth.get_user_id(access_token).read().decode('utf-8'))
                    if 'error' in response_user_id:
                        print('ERROR api_handler_directive.process.discovery.user_id: ' + response_user_id['error_description'])
                    user_id = response_user_id['user_id']
                    print('LOG api_handler_directive.process.discovery.user_id:', user_id)

                adr = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')

                # Get the list of endpoints associated with the user
                table = boto3.resource('dynamodb').Table('APISensorEndpointDetails')
                result = table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('UserId').eq(user_id)
                )

                for endpoint_details in result['Items']:

                    # We have an endpoint 
                    print('LOG api_handler_directive.process.discovery: Found:', endpoint_details['EndpointId'], 'for user:', user_id)

                    adr.add_payload_endpoint(
                        friendly_name=endpoint_details['FriendlyName'],
                        endpoint_id=endpoint_details['EndpointId'],
                        capabilities=json.loads(endpoint_details['Capabilities']),
                        display_categories=json.loads(endpoint_details['DisplayCategories']),
                        manufacturer_name=endpoint_details['ManufacturerName']
                    )

                response = adr.get()

        else:
            alexa_error_response = AlexaResponse(name='ErrorResponse')
            alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': 'Empty Body'})
            response = alexa_error_response.get()

        if response is None:
            # response set to None indicates an unhandled directive, review the logs
            alexa_error_response = AlexaResponse(name='ErrorResponse')
            alexa_error_response.set_payload({'type': 'INTERNAL_ERROR', 'message': 'Empty Response: No response processed. Unhandled Directive.'})
            response = alexa_error_response.get()

        print('LOG api_handler_directive.process.response -----')
        print(json.dumps(response))
        return response


def validate_response(response):
    valid = False
    try:
        with open('alexa_smart_home_message_schema.json', 'r') as schema_file:
            json_schema = json.load(schema_file)
            validate(response, json_schema)
        valid = True
    except SchemaError as se:
        print('LOG api_handler_directive.validate_response: Invalid Schema')
        print(se.context)
    except ValidationError as ve:
        print('LOG api_handler_directive.validate_response: Invalid Content')
        print(ve.context)

    return valid
