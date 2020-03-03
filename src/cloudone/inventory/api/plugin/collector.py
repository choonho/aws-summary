# -*- coding: utf-8 -*-
#
#   Copyright 2020 The SpaceONE Authors.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging

from cloudone.api.inventory.plugin import collector_pb2, collector_pb2_grpc
from cloudone.core.pygrpc import BaseAPI
from cloudone.core.pygrpc.message_type import *

_LOGGER = logging.getLogger(__name__)

class Collector(BaseAPI, collector_pb2_grpc.CollectorServicer):

    pb2 = collector_pb2
    pb2_grpc = collector_pb2_grpc

    def verify(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('CollectorService', metadata) as collector_svc:
            data = collector_svc.verify(params)
            return self.locator.get_info('CollectorVerifyInfo', data)


    def collect(self, request, context):
        params, metadata = self.parse_request(request, context)
        collector_svc: CollectorService = self.locator.get_service('CollectorService', metadata)

        with collector_svc:
            for resources in collector_svc.list_resources(params):
                for res in resources:
                    res = {
                        'state': (res['state']),
                        'message': '',
                        'resource_type': (res['resource_type']),
                        'match_rules': change_struct_type(res['match_rules']),
                        'replace_rules': change_struct_type(res['replace_rules']),
                        'resource': change_struct_type(res['resource'])
                    }
                    yield self.locator.get_info('ResourceInfo', res)
