# AWS Cloud Service Summary plugin (Beta)

aws-summary is starting point of AWS resource discovery and management. It collects various AWS services based on your AWS credentials.

# Introduction

This plugin can be installed at Inventory->Collector.

# Plugin Details

<img src="https://raw.githubusercontent.com/spaceone-dev/aws-summary/master/docs/aws-summary-screenshot-1.png" height="200">

This plugin can collector following resources per region:
* Number of EC2 with instance type
* Number of S3 buckets with summarized size
* Number of RDS like MySQL, DocumentDB
* Number of Lambda functions
* Number of Classic Load Balancer
* Number of ELB like ALB/NLB
* Number of DynamoDB

# Credentials
This plugin requires AWS credentials for collecting.

Parameter | Description | Option
---       | ---         | ---
aws_access_key_id | your_access_key_id  | Mandatory 
aws_secret_access_key | your_secret_access_key | Mandatory
project_id | your_project_id | Optional

<img src="https://raw.githubusercontent.com/spaceone-dev/aws-summary/master/docs/aws-summary-credential-1.png" height="200">

JSON example

~~~json
{"aws_access_key_id": "<YOUR AWS ACCESS KEY ID>", "aws_secret_access_key": "<YOUR AWS SECRET ACCESS KEY>"}
~~~

<img src="https://raw.githubusercontent.com/spaceone-dev/aws-summary/master/docs/aws-summary-credential-2.png" height="200">

# Development

This is guide for developer.
Docker is required development tool for build and test.

~~~bash
git clone https://github.com/spaceone-dev/aws-summary.git
cd aws-summary
make help
~~~

