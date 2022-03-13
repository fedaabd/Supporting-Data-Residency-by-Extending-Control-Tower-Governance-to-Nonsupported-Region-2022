# Supporting Data Residency by Extending AWS Control Tower Governance to Non-supported Regions 2022


AWS Control Tower is an AWS managed service that automates the creation of a well-architected multi-account AWS environment. This simplifies new account provisioning and centralized compliance for  your AWS Organization. With AWS Control Tower, builders can provision  new AWS accounts that conform to your company-wide policies in a few  clicks. Creating accounts using AWS Control Tower’s Account Factory is a single-threaded process at this point, customers must allow for the  current account creation process to complete before they can begin the  next account creation process.
In this repo, we demonstrate how you can extend the AWS Control Tower deployment to AWS regions which are not currently supported by AWS Control Tower. This will allow you to ensure governance in non-supported regions, and comply with local data localization requirements.
This solution uses the following AWS services:

AWS Control Tower
AWS CloudFormation
AWS Lambda
AWS Service Catalog
AWS Organizations

Prerequisites:

Audit and Log Archive account need to be in the PolicyStagingCustom OU temporarily to run the baseline code and then moved back to security OU
Make sure the non-supported region is enabled
Ensure CloudFormation templates stored in Amazon S3, have the following file directory: templates/baseline
