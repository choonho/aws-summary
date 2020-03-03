#! /usr/bin/env python3
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

__all__ = ["SummaryConnector"]

import os
import os.path
# AWS SDK for Python
import boto3
import json
import requests
import logging
import urllib.request
import time
import threading
import pprint

from datetime import datetime

from cloudone.core.transaction import Transaction
from cloudone.core.error import *
from cloudone.core.connector import BaseConnector

_LOGGER = logging.getLogger(__name__)


RESOURCES = ['cloudformation', 'cloudwatch', 'dynamodb', 'ec2', 'glacier', 'iam', 'opsworks', 's3', 'sns', 'sqs']

################################################
# Define local method here
# since REGION_SERVICES use method as value
################################################
def _find_ec2(service_name, client, resource):
    """ Find all EC2 instances

    Returns: dict
        {
            'total_count': N,
            'instances': {EC2_TYPE: Num of instances}
        }
    """
    resp = client.describe_instances()
    instance_groups = resp['Reservations']
    result = {}
    count = 0
    ec2_per_type = {}
    for instances in instance_groups:
        for instance in instances['Instances']:
            ec2_type = instance['InstanceType']
            ec2_type = ec2_type.replace('.','-')               # We cannot use . as key
            i_type = ec2_per_type.get(ec2_type, 0)
            i_type += 1
            ec2_per_type[ec2_type] = i_type
            count += 1
    result['total_count'] = count
    result['type'] = ec2_per_type
    return {service_name: result}
 
def _find_elb(service_name, client, resource):
    """ Find all ELBs

    Returns: dict
        {
            'total_count': N,
            'elb': {ELB_TYPE: Num of elbs}
        }
    """
    resp = client.describe_load_balancers()
    elb_groups = resp['LoadBalancerDescriptions']
    result = {}
    count = 0
    for elbs in elb_groups:
        elb_type = 'clb'
        count += 1
    result['total_count'] = count
    return {service_name: result}

def _find_elbv2(service_name, client, resource):
    """ Find all ALB, NLB
    """
    resp = client.describe_load_balancers()
    elb_groups = resp['LoadBalancers']
    result = {}
    count = 0
    elb_per_type = {}
    for elb in elb_groups:
        elb_type = elb['Type']
        instances = elb_per_type.get(elb_type, 0)
        instances += 1
        elb_per_type[elb_type] = instances
        count += 1
    result['total_count'] = count
    if count > 0:
        result['type'] = elb_per_type
    return {service_name: result}

def _find_dynamodb(service_name, client, resource):
    """ Find all DynamoDB

    Returns: dict
        {
            'total_count': N,
            'elb': {ELB_TYPE: Num of elbs}
        }
    """
    resp = client.list_tables()
    resource_groups = resp['TableNames']
    result = {}
    count = 0
    for resource in resource_groups:
        count += 1
    result['total_count'] = count
    return {service_name: result}

def _find_lambda(service_name, client, resource):
    """ Find all Lambda

    Returns: dict
        {
            'total_count': N,
            'runtime': {RUNTIME: Num of runtime}
        }
    """
    resp = client.list_functions()
    resource_groups = resp['Functions']
    result = {}
    count = 0
    for resource in resource_groups:
        count += 1
    result['total_count'] = count
    return {service_name: result}

def _find_rds(service_name, client, resource):
    """ Find all RDS

    Returns: dict
        {
            'total_count': N,
            'runtime': {RUNTIME: Num of runtime}
        }
    """
    resp = client.describe_db_clusters()
    resource_groups = resp['DBClusters']
    result = {}
    count = 0
    aurora_count = 0
    for resource in resource_groups:
        count += 1
        aurora_count += 1

    resp = client.describe_db_instances()
    resource_groups = resp['DBInstances']
    for resource in resource_groups:
        count += 1
        print(resource['Engine'])
    result['total_count'] = count
    return {service_name: result}



def _find_route53(service_name, client, resource):
    """ Find all Route53, number of hosted zone

    Returns: dict
        {
            'total_count': N,
            'runtime': {RUNTIME: Num of runtime}
        }
    """
    resp = client.list_hosted_zones()
    resource_groups = resp['HostedZones']
    result = {}
    count = 0
    for resource in resource_groups:
        count += 1
    result['total_count'] = count
    return {'global': {service_name: result}}


def _find_s3(service_name, client, resource):
    """ Find all S3 buckets

    Returns: dict
        {REGION_NAME: 's3': {
                        {
                        'total_count': N,
                        'buckets': {BUCKET_NAME: Num of instances}
                        }
                }
        }
    """
    s3 = resource

    def _get_location(bucket_name):
        response = client.get_bucket_location(Bucket=bucket_name)
        loc = response['LocationConstraint']
        if loc == None:
            return 'us-east-1'
        return loc

    def _get_bucket_info(bucket_name):
        
        bucket = s3.Bucket(bucket_name)
        total_size = 0
        obj_count = 0
        for object in bucket.objects.all():
            obj_count += 1
            total_size += object.size

        return obj_count, total_size/1024/1024/1024

    resp = client.list_buckets()
    buckets = resp['Buckets']
    result = {}
    for bucket in buckets:
        bucket_name = bucket['Name']
        location = _get_location(bucket_name)
        per_region = result.get(location, {})

        count_per_region = per_region.get('total_count', 0)
        type_per_region = per_region.get('type', {})

        total_size = type_per_region.get('total_size', 0)
        total_obj  = type_per_region.get('total_objects', 0)

        obj_count, bucket_size = _get_bucket_info(bucket_name)
        count_per_region += 1
        total_size += bucket_size
        total_obj  += obj_count

        per_region['type'] = {'total_size(GB)': total_size, 'total_objects': total_obj} 
        per_region['total_count'] = count_per_region
        result.update({location: per_region})

    
    s3_resource = {}
    for region_name, buckets in result.items():
        s3_resource[region_name] = {'s3': buckets}
    pprint.pprint(s3_resource)
    return s3_resource

# Find per region
REGION_SERVICES = {
    'ec2'       : _find_ec2,
    'elb'       : _find_elb,
    'elbv2'     : _find_elbv2,
    'dynamodb'  : _find_dynamodb,
    'lambda'    : _find_lambda,
    'rds'       : _find_rds,
}

# for test
#REGION_SERVICES = {
#    'elb'       : _find_elb,
#}

# Find at One time
GLOBAL_SERVICES = {
    's3' : _find_s3,
    'route53'   : _find_route53,
}

#GLOBAL_SERVICES = {
#    'route53'   : _find_route53,
#}

class SummaryConnector(BaseConnector):
    def __init__(self, transaction, config):
        super().__init__(transaction, config)
        self.lock = threading.Lock()
        self.result = {}

    def verify(self, options, credentials):
        self.cred = credentials
        # This is connection check for AWS
        self._set_connect(credentials)
        return "ACTIVE"
        #return self.conf

    def _set_connect(self, cred, region='ap-northeast-2', service='ec2'):
        """
        cred(dict)
            - aws_access_key_id
            - aws_secret_access_key
            - ...
        """
        self.session = boto3.Session(aws_access_key_id=cred['aws_access_key_id'],
                                    aws_secret_access_key=cred['aws_secret_access_key'])

        #proxy = self.conf.get('external_proxy', None)

        aws_conf = {}
        aws_conf['region_name'] = region

        # TODO: proxy mode
        #if proxy:
        #    endpoint_info = utils.parseEndpoint(proxy)
        #    aws_conf['config'] = Config(proxies={endpoint_info['protocol']: '%s:%s'%(endpoint_info['host'],endpoint_info['port'])})

        #    if endpoint_info['protocol'] == 'http':
        #        aws_conf['use_ssl'] = False
        if service in RESOURCES:
            self.resource = self.session.resource(service, **aws_conf)
            self.client = self.resource.meta.client
        else:
            self.client = self.session.client(service, region_name=region)

 
        #try:
        #    self.client.describe_key_pairs()

        #except Exception as e:
        #    raise ERROR_DRIVER(message='aws connection failed. Please check your authencation information.')
	
    def collect_info(self, query, region_id=None, zone_id=None, pool_id=None, project_id=None):
        def merge_dict(dict1, dict2):
            for region_name2, service2 in dict2.items():
                print("Merge at : ", region_name2)
                service1 = dict1.get(region_name2, {})
                service1.update(service2)
                dict1[region_name2] = service1
            pprint.pprint(dict1)
            return dict1

        def is_empty(resources):
            empty=True
            for k,v in resources.items():
                if v['total_count'] > 0:
                    return False
            return True

        client = self.session.client("sts")
        account_id = client.get_caller_identity()["Account"]
        print(f'ACCOUNT ID: {account_id}')

        # 0. Return CLOUD_SERVICE_TYPE
        yield _prepare_cloud_service_type()

        resource = _prepare_resource_schema()
        
        # Global Services
        result = {}
        for service, func in GLOBAL_SERVICES.items():
            params = {
                'service': service,
                'region': None,
                'session': self.session,
                'func': func,
                'result': self.result,
                'lock': self.lock
            }
            find_service(params)

        # Regional Services
        region_list = self._find_all_regions(self.cred)
        threads = []
        for region in region_list:
            print(f'Discover at {region}....')
            region_data = result.get(region, {})
            # Loop region
            for service, func in REGION_SERVICES.items():
                # Find service by func using thread
                params = {
                    'service': service,
                    'region': region,
                    'session': self.session,
                    'func': func,
                    'result': self.result,
                    'lock': self.lock
                }
                t = threading.Thread(target=find_service, args=(params,))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        # Clean-up garbage
        for region, summary in self.result.items():
            if is_empty(summary):
                continue
            print(region, summary)
            resource['data'] = summary
            resource['data'].update({'region_name': region, 'account_id': account_id})
            response = _prepare_response_schema()
            response['resource'].update(resource)
            yield response



    def _find_all_regions(self, cred):
        """ Find all AWS regions based on EC2
        """
        self._set_connect(cred)
        regions = self.client.describe_regions()
        region_list = []
        for region in regions['Regions']:
            region_list.append(region['RegionName'])
        #print(region_list)
        return region_list

def set_connect(session, region, service):
    aws_conf = {}
    aws_conf['region_name'] = region

    if service in RESOURCES:
        resource = session.resource(service, **aws_conf)
        client = resource.meta.client
    else:
        client = session.client(service, region_name=region)
        resource = None
    return client, resource

def find_service(params):
    """
    Args: params(dict) {
                    'service': str,
                    'region': str,
                    'session': object,
                    'func': object,
                    'result': dict,
                    'lock': Lock object
                }
    """     
    #print(params)
    client, resource = set_connect(params['session'], params['region'], params['service'])
    r = params['func'](params['service'], client, resource)
    if params['region'] == None:
        update_global_result(params['result'], None, r, params['lock'])
    else:
        update_result(params['result'], params['region'], r, params['lock'])

def update_global_result(result, region, data, lock):
    """ Update data at result using lock
    """
    try:
        lock.acquire()
        for region, region_data in data.items():
            region_data_orig = result.get(region, {})
            region_data_orig.update(region_data)
            result[region] = region_data_orig

    finally:
        lock.release()

def update_result(result, region, data, lock):
    """ Update data at result using lock
    """
    try:
        lock.acquire()

        region_data = result.get(region, {})
        region_data.update(data)
        result[region] = region_data

    finally:
        lock.release()





def _prepare_response_schema() -> dict:
    return {
        'state': 'SUCCESS',
        'resource_type': 'CLOUD_SERVICE',
        'match_rules': {
            '1': ['data.region_name', 'data.account_id', 'name', 'group', 'provider']
        },
        'replace_rules': {},
        'resource': {
            'cloud_service_type': 'Summary',
            'cloud_service_group': 'aws',
            'provider': 'SpaceONE'
        }
    }

def _prepare_cloud_service_type():
    return {
        'state': 'SUCCESS',
        'resource_type': 'CLOUD_SERVICE_TYPE',
        'match_rules': {
            '1': ['name', 'group', 'provider', 'account_id']
        },
        'replace_rules': {},
        'resource': {
            'name': 'Summary',
            'provider': 'SpaceONE',
            'group': 'aws',
            'data_source': [
                {
                    'name': 'Region Name',
                    'key': 'data.region_name'
                },
                {
                    'name': 'Account ID',
                    'key': 'data.account_id'
                },
                {
                    'name': 'EC2',
                    'key': 'data.ec2.total_count'
                },
                {
                    'name': 'S3',
                    'key': 'data.s3.total_count'
                },
                {
                    'name': 'RDS',
                    'key': 'data.rds.total_count'
                },
                {
                    'name': 'Lambda',
                    'key': 'data.lambda.total_count'
                },
                {
                    'name': 'CLB',
                    'key': 'data.elb.total_count'
                },
                {
                    'name': 'ALB/NLB',
                    'key': 'data.elbv2.total_count'
                },
                {
                    'name': 'DynamoDB',
                    'key': 'data.dynamodb.total_count'
                }
            ],
        }
    }


def _prepare_resource_schema() -> dict:
    return {
        'data': {
        },
        'metadata': {
            'details': [
                {
                    'name': 'AWS details',
                    'data_source': [
                        {
                            'name': 'Region name',
                            'key': 'data.region_name'
                        }
                    ]
                }
            ]
        }
    }

if __name__ == "__main__":
    import os
    aki = os.environ.get('AWS_ACCESS_KEY_ID', "<YOUR_AWS_ACCESS_KEY_ID>")
    sak = os.environ.get('AWS_SECRET_ACCESS_KEY', "<YOUR_AWS_SECRET_ACCESS_KEY>")
    cred = {
        'aws_access_key_id': aki,
        'aws_secret_access_key': sak
    }
    conn = SummaryConnector(Transaction(), cred)
    conn.verify({}, cred)
    resource_stream = conn.collect_info(query={})
    for resource in resource_stream:
        print(resource)

