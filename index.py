"""
Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0

AWS Disclaimer.

(c) 2019 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
This AWS Content is provided subject to the terms of the AWS Customer
Agreement available at https://aws.amazon.com/agreement/ or other written
agreement between Customer and Amazon Web Services, Inc.

Looks up VPC and associated subnets based on tags.
Returns the VPC and Subnet values back to the custom resource.

Runtime: python3.6
Last Modified: 2/6/2019
"""
from __future__ import print_function
from botocore.exceptions import ClientError
import boto3
import json
import logging
import os
import urllib3
import time
import ipaddress

EC2_CLIENT = boto3.client('ec2')
ec2 = boto3.resource('ec2')
SUCCESS = "SUCCESS"
FAILED = "FAILED"
http = urllib3.PoolManager()
VERBOSE = 1

def lambda_handler(event, context):
    """
    Do the work - order of operation

    1.) Delete the internet-gateway
    2.) Delete subnets
    3.) Delete route-tables
    4.) Delete network access-lists
    5.) Delete security-groups
    6.) Delete the VPC 
    """

    response_data = {}
    setup_logging()
    log.info('In Main Handler')
    log.info(json.dumps(event))
    print(json.dumps(event))

    if event['RequestType'] in ['Update', 'Create']:
        log.info('Event = ' + event['RequestType'])
        vpcs = get_default_vpcs(EC2_CLIENT)
        for vpc in vpcs:
            print("VPC Id:" + vpc)
            del_igw(ec2, vpc)
            del_sub(ec2, vpc)
            del_rtb(ec2, vpc)
            del_acl(ec2, vpc)
            del_sgp(ec2, vpc)
            del_vpc(ec2, vpc)
        send(event, context, 'SUCCESS', response_data)
    else:
        log.error("failed to run")
        send(event, context, 'FAILED', response_data)

    if event['RequestType'] in ['Delete']:
        log.info('Event = ' + event['RequestType'])

        send(event, context, 'SUCCESS', response_data)
def del_igw(ec2, vpcid):
  """ Detach and delete the internet-gateway """
  vpc_resource = ec2.Vpc(vpcid)
  igws = vpc_resource.internet_gateways.all()
  if igws:
    for igw in igws:
      try:
        print("Detaching and Removing igw-id: ", igw.id) if (VERBOSE == 1) else ""
        igw.detach_from_vpc(
          VpcId=vpcid
        )
        igw.delete(
          # DryRun=True
        )
      except boto3.exceptions.Boto3Error as e:
        print(e)

def del_sub(ec2, vpcid):
  """ Delete the subnets """
  vpc_resource = ec2.Vpc(vpcid)
  subnets = vpc_resource.subnets.all()
  default_subnets = [ec2.Subnet(subnet.id) for subnet in subnets if subnet.default_for_az]
  
  if default_subnets:
    try:
      for sub in default_subnets: 
        print("Removing sub-id: ", sub.id) if (VERBOSE == 1) else ""
        sub.delete(
          # DryRun=True
        )
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_rtb(ec2, vpcid):
  """ Delete the route-tables """
  vpc_resource = ec2.Vpc(vpcid)
  rtbs = vpc_resource.route_tables.all()
  if rtbs:
    try:
      for rtb in rtbs:
        assoc_attr = [rtb.associations_attribute for rtb in rtbs]
        if [rtb_ass[0]['RouteTableId'] for rtb_ass in assoc_attr if rtb_ass[0]['Main'] == True]:
          print(rtb.id + " is the main route table, continue...")
          continue
        print("Removing rtb-id: ", rtb.id) if (VERBOSE == 1) else ""
        table = ec2.RouteTable(rtb.id)
        table.delete(
          # DryRun=True
        )
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_acl(ec2, vpcid):
  """ Delete the network-access-lists """
  
  vpc_resource = ec2.Vpc(vpcid)      
  acls = vpc_resource.network_acls.all()

  if acls:
    try:
      for acl in acls: 
        if acl.is_default:
          print(acl.id + " is the default NACL, continue...")
          continue
        print("Removing acl-id: ", acl.id) if (VERBOSE == 1) else ""
        acl.delete(
          # DryRun=True
        )
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_sgp(ec2, vpcid):
  """ Delete any security-groups """
  vpc_resource = ec2.Vpc(vpcid)
  sgps = vpc_resource.security_groups.all()
  if sgps:
    try:
      for sg in sgps: 
        if sg.group_name == 'default':
          print(sg.id + " is the default security group, continue...")
          continue
        print("Removing sg-id: ", sg.id) if (VERBOSE == 1) else ""
        sg.delete(
          # DryRun=True
        )
    except boto3.exceptions.Boto3Error as e:
      print(e)

def del_vpc(ec2, vpcid):
  """ Delete the VPC """
  vpc_resource = ec2.Vpc(vpcid)
  try:
    print("Removing vpc-id: ", vpc_resource.id)
    vpc_resource.delete(
      # DryRun=True
    )
  except boto3.exceptions.Boto3Error as e:
      print(e)
      print("Please remove dependencies and delete VPC manually.")
  #finally:
  #  return status



def get_default_vpcs(client):
  vpc_list = []
  vpcs = client.describe_vpcs(
    Filters=[
      {
          'Name' : 'isDefault',
          'Values' : [
            'true',
          ],
      },
    ]
  )
  vpcs_str = json.dumps(vpcs)
  resp = json.loads(vpcs_str)
  data = json.dumps(resp['Vpcs'])
  vpcs = json.loads(data)
  
  for vpc in vpcs:
    vpc_list.append(vpc['VpcId'])  
  
  return vpc_list

def setup_logging():
    """Setup Logging."""
    global log
    log = logging.getLogger()
    log_levels = {'INFO': 20, 'WARNING': 30, 'ERROR': 40}

    if 'logging_level' in os.environ:
        log_level = os.environ['logging_level'].upper()
        if log_level in log_levels:
            log.setLevel(log_levels[log_level])
        else:
            log.setLevel(log_levels['ERROR'])
            log.error("The logging_level environment variable is not set \
                      to INFO, WARNING, or ERROR. \
                      The log level is set to ERROR")
    else:
        log.setLevel(log_levels['ERROR'])
        log.warning('The logging_level environment variable is not set.')
        log.warning('Setting the log level to ERROR')
    log.info('Logging setup complete - set to log level '
             + str(log.getEffectiveLevel()))


def send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False, reason=None):
    responseUrl = event['ResponseURL']

    print(responseUrl)

    responseBody = {
        'Status' : responseStatus,
        'Reason' : reason or "See the details in CloudWatch Log Stream: {}".format(context.log_stream_name),
        'PhysicalResourceId' : physicalResourceId or context.log_stream_name,
        'StackId' : event['StackId'],
        'RequestId' : event['RequestId'],
        'LogicalResourceId' : event['LogicalResourceId'],
        'NoEcho' : noEcho,
        'Data' : responseData
    }

    json_responseBody = json.dumps(responseBody)

    print("Response body:")
    print(json_responseBody)

    headers = {
        'content-type' : '',
        'content-length' : str(len(json_responseBody))
    }

    try:
        response = http.request('PUT', responseUrl, headers=headers, body=json_responseBody)
        print("Status code:", response.status)


    except Exception as e:

        print("send(..) failed executing http.request(..):", e)