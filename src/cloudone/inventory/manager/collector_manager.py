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


__all__ = ['CollectorManager']

import logging

from datetime import datetime

from cloudone.core import config
from cloudone.core.error import *
from cloudone.core.manager import BaseManager

_LOGGER = logging.getLogger(__name__)

class CollectorManager(BaseManager):
    def __init__(self, transaction):
        super().__init__(transaction)

        
    ###################
    # Verify
    ###################
    def verify(self, options, credentials):
        connector = self.locator.get_connector('SummaryConnector')
        r = connector.verify(options, credentials)
        # ACTIVE/UNKNOWN
        return r

    def list_resources(self, options, credentials, filters):
        # call ec2 connector

        connector = self.locator.get_connector('SummaryConnector')
        connector.verify(options, credentials)

        # make query, based on options, credentials, filter
        query = filters

        #
        region_id = None
        zone_id = None
        pool_id = None
        project_id = None

        # Special field for plugin in credentials
        if 'region_id' in credentials:
            region_id = credentials['region_id']
        if 'zone_id' in credentials:
            zone_id = credentials['zone_id']
        if 'pool_id' in credentials:
            pool_id = credentials['pool_id']
        # WARNING
        # project_id will be deprecated after 1.0
        if 'identity.project_id' in credentials:
            project_id = credentials['identity.project_id']

        return connector.collect_info(query, region_id, zone_id, pool_id, project_id)
