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
import os
import sys
import traceback
from endpoint_cloud import ApiHandler, ApiResponse, ApiResponseBody


def handler(request, context):

    # Dump the request for logging - check the CloudWatch logs
    print('lambda_handler request  -----')
    print(json.dumps(request))

    # An API Handler to handle internal operations to the endpoints
    api_handler = ApiHandler()

    # An API Response crafted to return to the caller - in this case the API Gateway
    # The API Gateway expects a specially formatted response
    api_response = ApiResponse()

    if context is not None:
        print('lambda_handler context  -----')
        print(context)

    try:
        # Get the Client ID, and Client Secret
        env_client_id = os.environ.get('client_id', None)
        env_client_secret = os.environ.get('client_secret', None)

        if env_client_id is None or env_client_secret is None:
            api_response.statusCode = 403
            api_response.body = ApiResponseBody(
                result="ERR", 
                message="Environment variable is not set: client_id:{0} client_secret:{1}".format(env_client_id, env_client_secret))
            return api_response.get()

        # Route the inbound request by evaluating for the resource and HTTP method
        resource = request['path']
        http_method = request["httpMethod"]

        # CORS Preflight request
        if http_method == 'OPTIONS':
            api_response.statusCode = 204
            api_response.headers['Access-Control-Allow-Origin'] = '*'
            api_response.headers['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, PUT'
            api_response.headers['Access-Control-Allow-Headers'] = 'x-api-key, Content-Type'
            api_response.headers['Allow'] = 'CONVERT'

        # POST to directives : Process an Alexa Directive - This will be used to implement Endpoint behavior and state
        elif http_method == 'POST' and resource == '/directives':
            response = api_handler.directive.process(request, env_client_id, env_client_secret)
            if response['event']['header']['name'] == 'ErrorResponse':
                error_message = response['event']['payload']['message']['error_description']
                api_response.statusCode = 500
                api_response.body = ApiResponseBody(result="ERR", message=error_message)
                return api_response.get()
            else:
                api_response.statusCode = 200
                api_response.body = json.dumps(response)

        # POST to endpoints : Create an Endpoint
        elif http_method == 'POST' and resource == '/endpoints':
            response = api_handler.endpoint.create(request)
            api_response.statusCode = 200
            api_response.body = json.dumps(response)

        # GET endpoints : List Endpoints
        elif http_method == 'GET' and resource == '/endpoints':
            response = api_handler.endpoint.read()
            api_response.statusCode = 200
            api_response.body = json.dumps(response)

        # DELETE endpoints : Delete an Endpoint
        elif http_method == 'DELETE' and resource == '/endpoints':
            response = api_handler.endpoint.delete(request)
            api_response.statusCode = 200
            api_response.body = json.dumps(response)

        # UPDATE endpoints : Delete an Endpoint
        elif http_method == 'PUT' and resource == '/endpoints':
            response = api_handler.endpoint.update(request)
            api_response.statusCode = 200
            api_response.body = json.dumps(response)

        # POST to event : Create an Event
        elif http_method == 'POST' and resource == '/events':
            response = api_handler.event.create(request)
            print('LOG api.index.handler.request.api_handler.event.create.response:', response)
            api_response.statusCode = 200
            api_response.body = json.dumps(response)

        else:
            print('LOG api.index.handler.request')
            api_response.statusCode = 400
            api_response.body = ApiResponseBody(result="ERR", message='Path and http method do not match')

    except KeyError as key_error:
        # For a key Error, return an error message and HTTP Status of 400 Bad Request
        message_string = "KeyError: " + str(key_error)

        # Dump a traceback to help in debugging
        print('TRACEBACK:START')
        traceback.print_tb(sys.exc_info()[2])
        print('TRACEBACK:END')

        api_response.statusCode = 400
        api_response.body = ApiResponseBody(result="ERR", message=message_string)

    print('LOG api.index.handler.api_handler -----')
    print(json.dumps(api_response.get()))

    return api_response.get()
