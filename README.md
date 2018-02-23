# AWS Lambda Heartbeat Patching

### by Cory Burns

## What this is

This is a small bit of Python 3.6 code designed to run in AWS Lambda, executed
by a CURL request to an AWS API Gateway.

This was written to help differentiate failovers in a customer's active/passive
cluster managed by heartbeat from "unknown" failovers and failovers caused by
Select Patching via BigFix.

Although this was created for a specific customer's request, it is customer
agnostic and can be used with any heartbeat cluster (with some caveats)

## How to use this

You need to create an AWS Lambda function that is executed by an API Gateway.  
You will need to create an SNS Topic, and assign subscriptions to that topic.  
These subscriptions should include the customer's email addresses if they wish 
to be notified as well as any Support or Operations teams that may manage the server.

You also need to create an API key.

To execute this code you will need to add a CURL request in the heartbeat config
on both servers.  This should replace any smtp() requests in the heartbeat 
config.  An example config is below:

curl -X POST -H "x-api-key: [AWS API KEY]" -H "Content-Type: application/json" -d '{"hostname":"[HOSTNAME]"}' https://[AWSAPIURL]/[LAMBDAFUNCTION]

Replace all the stuff in brackets (including the brackets themselves) with the 
appropriate information.  You can typically get the AWSPAIURL/LAMBDAFUNCTION 
from Lambda itself.

You should define your patching groups in the lambda_handler() function.  I have 
included sample code for that section already.  Some things to note:

* Do not change the hostname line; this pulls from the JSON that your CURL 
request pushes to AWS.
* The servername/hostname in PatchCluster() and setPatching() are strings and 
as such should be encapsulated in quotes
* The patching date follows WEEK OF THE MONTH (1 - 4), DAY OF THE WEEK (0 - 6) 
(starting on MONDAY) format and are ints and should NOT be encapsulated by any 
quotes.  I know that's kind of confusing because DOTW starts both on Monday and 
with 0 but that's just the way it is.

The actual email that is sent is defined in the class.  I have tried to make it 
as generic as possible but you may need to edit it.  I am hoping to make this 
better in a future release.

## Caveats

This function really only works with clusters of two servers.  This is normal for 
my company's configuration and is really the only setup supported by heartbeat, 
but some customers may have odd solutions such as a round robin with 3 or more 
servers.  In this case this script will not work properly, as it only expects two 
servers.  I may update it to be more flexible in the future.
