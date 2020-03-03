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

from cloudone.core.error import *
from cloudone.core.service import *

from cloudone.inventory.error import *

from cloudone.core.pygrpc.message_type import *

from cloudone.inventory.manager.collector_manager import CollectorManager

_LOGGER = logging.getLogger(__name__)

FILTER_FORMAT = [
]

SUPPORTED_RESOURCE_TYPE = ['CLOUD_SERVICE', 'CLOUD_SERVICE_TYPE']

@authentication_handler
class CollectorService(BaseService):
    def __init__(self, metadata):
        super().__init__(metadata)

    @transaction
    @check_required(['options','credentials'])
    def verify(self, params):
        """ verify options capability
        Args:
            params
              - options
              - credentials: may be empty dictionary

        Returns:

        Raises:
            ERROR_NOT_FOUND: 
        """
        manager = self.locator.get_manager('CollectorManager')
        options = params['options']
        credentials = params['credentials']
        active = manager.verify(options, credentials)
        _LOGGER.debug(active)
        capability = {
            'filter_format':FILTER_FORMAT,
            'supported_resource_type' : SUPPORTED_RESOURCE_TYPE
            }
        return {'options': capability}

    @transaction
    @check_required(['options','credentials', 'filter'])
    def list_resources(self, params):
        """ Get quick list of resources
        
        Args:
            params:
                - options
                - credentials
                - filter

        Returns: list of resources
        """
        manager = self.locator.get_manager('CollectorManager')
        options = params['options']
        credentials = params['credentials']
        filters = params['filter']
        yield manager.list_resources(options, credentials, filters)
