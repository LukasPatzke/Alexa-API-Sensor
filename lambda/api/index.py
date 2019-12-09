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

import boto3
import json
import os
from datetime import datetime, timedelta
import urllib.request
from alexa.skills.smarthome import AlexaResponse
from endpoint_cloud.api_auth import ApiAuth
from endpoint_cloud import ApiResponse, ApiResponseBody

aws_dynamodb = boto3.client('dynamodb')


def handler(request, context):

    # Dump the request for logging - check the CloudWatch logs
    print('lambda_handler request  -----')
    print(json.dumps(request))

    # An API Response crafted to return to the caller - in this case the API Gateway
    # The API Gateway expects a specially formatted response
    api_response = ApiResponse()

    if context is not None:
        print('lambda_handler context  -----')
        print(context)

    # Get the Client ID, and Client Secret
    env_client_id = os.environ.get('client_id', None)
    env_client_secret = os.environ.get('client_secret', None)

    if env_client_id is None or env_client_secret is None:
        api_response.statusCode = 403
        api_response.body = ApiResponseBody(
            result="ERR", 
            message="Environment variable is not set: client_id:{0} client_secret:{1}".format(env_client_id, env_client_secret))
        return api_response.get()

    path = request['path']

    json_body = request['body']
    if json_body:
        json_object = json.loads(json_body)

    if path == '/events':
        # Handle change report event request
        user_id = json_object['endpoint']['userId']
        endpoint_id = json_object['endpoint']['endpointId']

        # Get the User access_token from User ID
        token = get_user_info(user_id)

        print('Sending StateReport on endpoint', endpoint_id)

        changereport_response = AlexaResponse(
            name='ChangeReport', 
            endpoint_id=endpoint_id, 
            token=token)
        # Always return state 'DETECTED' 
        property_change = changereport_response.create_payload_change_property(
            namespace='Alexa.ContactSensor',
            name='detectionState',
            value='DETECTED'
        )
        changereport_response.add_payload_change(
            properties=[property_change]
        )
        changereport_response.add_context_property(
            namespace='Alexa.EndpointHealth',
            name='connectivity',
            value='OK'
        )

        return send_event(token, changereport_response.get())

    elif path == '/directives':
        # Handle Alexa skill request

        directive = json_object['directive']
        
        # Validate we have an Alexa directive
        if 'directive' not in json_object:
            api_response.statusCode = 500
            api_response.body = ApiResponseBody(
                result="ERR", 
                message="Missing key: directive, Is the request a valid Alexa Directive?")
            return api_response.get()

        # Check the payload version
        payload_version = directive['header']['payloadVersion']
        if payload_version != '3':
            api_response.statusCode = 500
            api_response.body = ApiResponseBody(
                result="ERR", 
                message="This skill only supports Smart Home API version 3")
            return api_response.get()

        # Crack open the request and see what is being requested
        name = directive['header']['name']
        namespace = directive['header']['namespace']

        # Handle the incoming request from Alexa based on the namespace

        if namespace == 'Alexa.Authorization':
            if name == 'AcceptGrant':
                # Note: This sample accepts any grant request
                # In your implementation you would use the code and token to get and store access tokens
                grant_code = directive['payload']['grant']['code']
                grantee_token = directive['payload']['grantee']['token']

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
                        api_response.statusCode = 500
                        api_response.body = ApiResponseBody(
                            result="ERR", 
                            message=response_user_id)
                        return api_response.get()

                    user_id = response_user_id['user_id']
                    print('LOG api_handler_directive.process.authorization.user_id:', user_id)

                # Get the Access and Refresh Tokens
                api_auth = ApiAuth()
                print('grant_code', grant_code, 'client_id', env_client_id, 'client_secret', env_client_secret)
                response_token = api_auth.get_access_token(grant_code, env_client_id, env_client_secret)
                response_token_string = response_token.read().decode('utf-8')
                print('LOG api_handler_directive.process.authorization.response_token_string:', response_token_string)
                response_object = json.loads(response_token_string)

                if 'error' in response_object:
                    api_response.statusCode = 500
                    api_response.body = ApiResponseBody(
                        result="ERR", 
                        message=response_object)
                    return api_response.get()

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
                        'ClientId': env_client_id,
                        'ClientSecret': env_client_secret,
                        'ExpirationUTC': expiration_utc.strftime("%Y-%m-%dT%H:%M:%S.00Z"),
                        'RefreshToken': refresh_token,
                        'TokenType': token_type
                    }
                )

                if result['ResponseMetadata']['HTTPStatusCode'] == 200:
                    print('LOG api_handler_directive.process.authorization.SampleUsers.put_item:', result)
                    api_response.statusCode = 200
                    aar = AlexaResponse(namespace='Alexa.Authorization', name='AcceptGrant.Response')
                else:
                    error_message = 'Error creating User'
                    print('ERR api_handler_directive.process.authorization', error_message)
                    api_response.statusCode = 500
                    aar = AlexaResponse(name='ErrorResponse')
                    aar.set_payload({'type': 'INTERNAL_ERROR', 'message': error_message})

                api_response.body = json.dumps(aar.get())
                return api_response.get()

        if namespace == 'Alexa.Discovery':
            if name == 'Discover':
                adr = AlexaResponse(namespace='Alexa.Discovery', name='Discover.Response')
                capability_alexa = adr.create_payload_endpoint_capability()
                capability_alexa_contactsensor = adr.create_payload_endpoint_capability(
                    interface='Alexa.ContactSensor',
                    supported=[{'name': 'detectionState'}],
                    proactively_reported=True,
                    retrievable=True)
                capability_alexa_endpointhealth = adr.create_payload_endpoint_capability(
                    interface='Alexa.EndpointHealth',
                    supported=[{'name': 'connectivity'}],
                    proactively_reported=True,
                    retrievable=True)
                adr.add_payload_endpoint(
                    friendly_name='API Sensor 1',
                    endpoint_id='api-sensor-01',
                    description='Sample API Sensor',
                    display_categories=['CONTACT_SENSOR'],
                    capabilities=[capability_alexa, capability_alexa_contactsensor, capability_alexa_endpointhealth])
                api_response.statusCode = 200
                api_response.body = json.dumps(adr.get())
                return api_response.get()

        if namespace == 'Alexa':
            if name == 'ReportState':
                correlation_token = directive['header']['correlationToken']
                token = directive['endpoint']['scope']['token']
                endpoint_id = directive['endpoint']['endpointId']

                # Get the User ID from the access_token
                response_user_id = json.loads(ApiAuth.get_user_id(token).read().decode('utf-8'))

                print('Sending StateReport for', response_user_id, 'on endpoint', endpoint_id)

                statereport_response = AlexaResponse(
                    name='StateReport', 
                    endpoint_id=endpoint_id, 
                    correlation_token=correlation_token, 
                    token=token)
                # Always return state 'NOT_DETECTED' 
                statereport_response.add_context_property(
                    namespace='Alexa.ContactSensor',
                    name='detectionState',
                    value='NOT_DETECTED'
                )
                statereport_response.add_context_property(
                    namespace='Alexa.EndpointHealth',
                    name='connectivity',
                    value='OK'
                )
                api_response.statusCode = 200
                api_response.body = json.dumps(statereport_response.get())
                return api_response.get()
    else:
        api_response.statusCode = 500
        api_response.body = ApiResponseBody(
            result="ERR", 
            message="No known path in request: {0}".format(request))
        return api_response.get()

def is_token_expired(expiration_utc):
    now = datetime.utcnow().replace(tzinfo=None)
    then = datetime.strptime(expiration_utc, "%Y-%m-%dT%H:%M:%S.00Z")
    is_expired = now > then
    if is_expired:
        return is_expired
    seconds = (now - then).seconds
    is_soon = seconds < 30  # Give a 30 second buffer for expiration
    return is_soon

def get_user_info(user_id):
    print('LOG event.create.get_user_info -----')
    table = boto3.resource('dynamodb').Table('APISensorUsers')
    result = table.get_item(
        Key={
            'UserId': user_id
        },
        AttributesToGet=[
            'UserId',
            'AccessToken',
            'ClientId',
            'ClientSecret',
            'ExpirationUTC',
            'RefreshToken',
            'TokenType'
        ]
    )

    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        if 'Item' in result:
            print('LOG event.create.get_user_info.SampleUsers.get_item -----')
            print(str(result['Item']))
            if 'ExpirationUTC' in result['Item']:
                expiration_utc = result['Item']['ExpirationUTC']
                token_is_expired = is_token_expired(expiration_utc)
            else:
                token_is_expired = True
            print('LOG event.create.send_event.token_is_expired:', token_is_expired)
            if token_is_expired:
                # The token has expired so get a new access token using the refresh token
                refresh_token = result['Item']['RefreshToken']
                client_id = result['Item']['ClientId']
                client_secret = result['Item']['ClientSecret']

                api_auth = ApiAuth()
                response_refresh_token = api_auth.refresh_access_token(refresh_token, client_id, client_secret)
                response_refresh_token_string = response_refresh_token.read().decode('utf-8')
                response_refresh_token_object = json.loads(response_refresh_token_string)

                # Store the new values from the refresh
                access_token = response_refresh_token_object['access_token']
                refresh_token = response_refresh_token_object['refresh_token']
                token_type = response_refresh_token_object['token_type']
                expires_in = response_refresh_token_object['expires_in']

                # Calculate expiration
                expiration_utc = datetime.utcnow() + timedelta(seconds=(int(expires_in) - 5))

                print('access_token', access_token)
                print('expiration_utc', expiration_utc)

                result = table.update_item(
                    Key={
                        'UserId': user_id
                    },
                    UpdateExpression="set AccessToken=:a, RefreshToken=:r, TokenType=:t, ExpirationUTC=:e",
                    ExpressionAttributeValues={
                        ':a': access_token,
                        ':r': refresh_token,
                        ':t': token_type,
                        ':e': expiration_utc.strftime("%Y-%m-%dT%H:%M:%S.00Z")
                    },
                    ReturnValues="UPDATED_NEW"
                )
                print('LOG event.create.send_event.SampleUsers.update_item:', str(result))

                # TODO Return an error here if the token could not be refreshed
            else:
                # Use the stored access token
                access_token = result['Item']['AccessToken']
                print('LOG Using stored access_token:', access_token)

            return access_token

def send_event(token, payload):

    payload = json.dumps(payload)
    print('LOG api_handler_event.send_event.payload:')
    print(payload)

    # TODO Map to correct endpoint for Europe: https://api.eu.amazonalexa.com/v3/events
    # TODO Map to correct endpoint for Far East: https://api.fe.amazonalexa.com/v3/events
    alexa_event_gateway_uri = 'https://api.eu.amazonalexa.com/v3/events'
    headers = {
        'Authorization': "Bearer " + token,
        'Content-Type': "application/json;charset=UTF-8",
        'Cache-Control': "no-cache"
    }
    data = bytes(payload, encoding="utf-8")
    req = urllib.request.Request(url=alexa_event_gateway_uri, data=data, headers=headers)
    result = urllib.request.urlopen(req).read().decode("utf-8")
    response = json.loads(result)
    print("LOG skill.index.send_event.response -----")
    print(json.dumps(response))
    return response


def set_device_state(endpoint_id, state, value):
    attribute_key = state + 'Value'
    response = aws_dynamodb.update_item(
        TableName='SampleSmartHome',
        Key={'ItemId': {'S': endpoint_id}},
        AttributeUpdates={attribute_key: {'Action': 'PUT', 'Value': {'S': value}}})
    print(response)
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        return True
    else:
        return False
