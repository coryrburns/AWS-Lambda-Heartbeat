import boto3
from datetime import date
import calendar
import json

class PatchCluster:
    """A class that will check the current date against an individual server's specified patch date
    
    This is typically going to be used in a cluster managed by heartbeat or something similar that can send
    a CURL request to an AWS API in order to execute the lambda function this class will reside in."""
    
    def __init__(self, primaryServer, secondaryServer):
        """Sets the primary and secondary server names in this cluster"""
        self.primary   = primaryServer
        self.secondary = secondaryServer
    
    def setPatching(self, hostname, weekOfMonth, dayInt):
        """Assigns a patching date to a server; checks the hostname against the already assigned servers"""
        if hostname == self.primary:
            self.primary_week = weekOfMonth
            self.primary_day  = dayInt
        elif hostname == self.secondary:
            self.secondary_week = weekOfMonth
            self.secondary_day  = dayInt
        else:
            return("Invalid Server, please use previously assigned hostname")
    
    def week_of_month(self, tgtdate):
        """Prints the week of the month in an integer
        Assumes weeks start on Monday
        
        Shamlessly stolen from user 'you cad sir' at
        http://stackoverflow.com/questions/7029261/python-number-of-the-week-in-a-month/7029955#7029955
        """
        
        days_this_month = calendar.mdays[tgtdate.month]
        for i in range(1, days_this_month):
            d = date(tgtdate.year, tgtdate.month, i)
            if d.day - d.weekday() > 0:
                startdate = d
                break
            
        # now we canuse the modulo 7 appraoch
        return (tgtdate - startdate).days //7 + 1
    
    def patchingNotification(self, hostname, arn, subject):
        """Sends an SNS notification based off if today is a patching day
        Requires the hostname to be sent via JSON by the CURRENTLY active server (e.g. whatever server is running
        after failover.
        
        Example CURL request:
        curl -X POST -H "x-api-key: [AWS API KEY]" -H "Content-Type: application/json" -d '{"hostname":"[HOSTNAME]"}' https://[AWSAPIURL]/[LAMBDAFUNCTION]
        """
        today    = date.today()
        cur_week = self.week_of_month(today)
        cur_day  = date.weekday(today)
        
        email_patch = """%s has failed over.  Server %s is currently the active host.
                
This was likely due to patching.  DevOps will follow up during regular business hours to verify.
                
Please reach out tyour Support Team if you notice any errors or issues in the meantime.
                
This is an automated message."""

        email_no_patch = """%s has failed over.  Server %s is currently the active host.
                
There was no known patching causing this event.  DevOps will investigate during regular business hours to verify.
                
Please reach out tyour Support Team if you notice any errors or issues in the meantime.
                
This is an automated message."""
        
        if hostname == self.primary:
            if cur_week == self.primary_week and cur_day == self.primary_day:
                email  = email_patch % (self.secondary, self.primary)
                client = boto3.client('sns')
                response = client.publish(
                    TopicArn=arn,
                    Subject=subject,
                    Message=email
                )
            else:
                email  = email_no_patch % (self.secondary, self.primary)
                client = boto3.client('sns')
                response = client.publish(
                    TopicArn=arn,
                    Subject=subject,
                    Message=email
                )
        elif hostname == self.secondary:
            if cur_week == self.secondary_week and cur_day == self.secondary_day:
                email  = email_patch % (self.primary, self.secondary)
                client = boto3.client('sns')
                response = client.publish(
                    TopicArn=arn,
                    Subject=subject,
                    Message=email
                )
            else:
                email = email_no_patch % (self.primary, self.secondary)
                client = boto3.client('sns')
                response = client.publish(
                    TopicArn=arn,
                    Subject=subject,
                    Message=email
                )
        else:
            print("Invalid hostname.")


def lambda_handler(event, context):
    
    hostname = json.loads(json.loads(json.dumps(event))['body'])['hostname'] # DO NOT CHANGE THIS
    arn='ARN' # The ARN for the SNS you are sending to
    subject='Customer Failover Notification'
    
    varnish = PatchCluster("cluster01-a", "cluster01-b")
    varnish.setPatching("cluster01-a", 2, 2) # Second Wednesday of the month
    varnish.setPatching("cluster01-b", 3, 2) # Third Wednesday of the month
    
    varnish.patchingNotification(hostname, arn, subject)
    
    return { 
            "statusCode": 200, 
            "headers": {"Content-Type": "application/json"},
            "body": "Lambda Execution Successful"
        }