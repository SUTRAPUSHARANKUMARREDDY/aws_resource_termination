import boto3
import time
from datetime import datetime, timedelta
from dateutil.tz import gettz
import json
import constant
import requests


def send_slack_message(slack_webhook_url, slack_message):
  print('>send_slack_message:slack_message:'+slack_message)
  slack_payload = {'text': slack_message}
  print('>send_slack_message:posting message to slack channel')
  response = requests.post(constant.slack_webhook_url, json.dumps(slack_payload))
  response_json = response.text
  print('>send_slack_message:response after posting to slack:'+str(response_json))



instance_id_list = []
instance_name_list = []

def find_running_ec2instances():
    send_message_to_slack = 0
    notification_message = ''
    message1 = 'The Following EC2 instance(s) will be Terminated : \n'
    message3 = 'The Following EC2 instance(s) are Terminated: \n'
    client = boto3.client("ec2", region_name='us-west-2')
    custom_filter = [
        {'Name': 'instance-state-name', 'Values': ['running']},
        {'Name': 'tag:TEAM_LOCATION','Values': ['INDIA']},
        {'Name': 'tag:SHUTDOWN', 'Values': ['DAILY']}
    ]
    response = client.describe_instances(Filters=custom_filter)
    instance_id_list = []
    instance_name_list = []
    format = "%d/%m/%Y"
    inst_cnt = 0
    instance_name_tag = ""
    end_date_str = ""
    for groups in response['Reservations']:
        num_running_ec2_instances = len(groups['Instances'])
        if num_running_ec2_instances > 0:
            va= groups['Instances']
            for i in va:
                if 'Tags' in i:
                    dict1 = {}
                    for tag in i['Tags']:
                        dict1[tag["Key"]] = tag["Value"]
                        if ( tag["Key"] == "Name" ):
                            instance_name_tag = tag['Value']
                            
                        if ( tag["Key"] == "END_DATE" ):
                            end_date_str = tag['Value']

                    if end_date_str == "" or end_date_str == "NA" or end_date_str == "FOREVER":
                        print("Instance " + instance_name_tag + "Not included for termination process")
                    else:
                        end_date = time.strptime(end_date_str, "%d/%m/%Y")
                        today = datetime.now(tz=gettz('Asia/Kolkata'))
                        tomorrow = today + timedelta(days=1)
                        today_str= today.strftime(format)
                        tomorrow_str = tomorrow.strftime(format)
                        today_date = time.strptime(today_str, "%d/%m/%Y")
                        tomorrow_date = time.strptime(tomorrow_str, "%d/%m/%Y")
                        if end_date == today_date:
                            send_message_to_slack = 1
                            print("To be stopped tomorrow: " + instance_name_tag)
                            if "POC" in dict1:
                                ec2_POC = dict1["POC"]
                            else:
                                ec2_POC = "No POC"
                            ec2_info = ', POC:' + ec2_POC
                            ec2_info = ':point_right: Name :' + instance_name_tag + ec2_info
                            ec2_info = ec2_info + ", InstanceId: " + i["InstanceId"]
                            ec2_info = ec2_info + ", *END_DATE: " + end_date_str +"*"
                            message1 += ec2_info + '\n'
                            inst_cnt = inst_cnt + 1
                        elif end_date == tomorrow_date:
                            send_message_to_slack = 1
                            print("To be stopped Day After Tomorrow: " + instance_name_tag)
                            if "POC" in dict1:
                                ec2_POC = dict1["POC"]
                            else:
                                ec2_POC = "No POC"
                            ec2_info = ', POC:' + ec2_POC
                            ec2_info = ':point_right: Name :' + instance_name_tag + ec2_info
                            ec2_info = ec2_info + ", InstanceId: " + i["InstanceId"]
                            ec2_info = ec2_info + ", *END_DATE: " + end_date_str +"*"
                            message1 += ec2_info + '\n'
                            inst_cnt = inst_cnt + 1
                        else:
                            print("No Instances to be Terminate soon")
                        
                        
                        if end_date < today_date:
                            send_message_to_slack = 1
                            if "POC" in dict1:
                                ec2_POC = dict1["POC"]
                            else:
                                ec2_POC = "No POC"
                            ec2_terminate_info = ', POC:' + ec2_POC
                            if "Name" in dict1:
                               ec2_instance_name = dict1["Name"]
                            else:
                                ec2_instance_name = "No Name"
                            ec2_terminate_info = ':point_right: Name:' + ec2_instance_name + ec2_terminate_info
                            ec2_terminate_info = ec2_terminate_info + ", InstanceId: " + i["InstanceId"]
                            ec2_terminate_info = ec2_terminate_info + ", *END_DATE: " + end_date_str +"*"
                            instance_id_list.append(i['InstanceId'])
                            instance_name_list.append(instance_name_tag)
                            inst_cnt = inst_cnt + 1
                            message3 += ec2_terminate_info + '\n'
                        else:
                            print("No instance to terminate")
                        
    print(instance_id_list)
    print(instance_name_list)
    notification_message += message1 + message3
    
    if inst_cnt >= 1:  
        def terminate_ec2(instance_id_list):
            ec2_terminate = boto3.client("ec2", region_name='us-west-2')
            for instance in instance_id_list:
                print(instance)
                ec2_terminate.modify_instance_attribute(
                    DisableApiTermination={
                        'Value': False
                    },
                    InstanceId=instance
                )
                ec2_terminate.terminate_instances(
            InstanceIds=[
                instance,
            ])
    else:
        print("There is no instance to Terminate")
    
    if inst_cnt >= 1:  
        def delete_rules_target(instance_name_list):
            rules_dict = {}
            taget_grp_dict = {}
            instance_name_alb = ""
            client = boto3.client("elbv2", region_name='us-west-2')
            rules_array = client.describe_rules(ListenerArn="arn:aws:elasticloadbalancing:us-west-2:920349478710:listener/app/Non-PlatformLB2/42c671e0716a4d8d/e1cc0b10d17ce4d2")
            for rule in rules_array['Rules']:
                rule_arn = rule['RuleArn']
                if ( rule['IsDefault'] == False ):
                    for condition in rule['Conditions']:
                        if ( condition['Field'] == "host-header" ):
                            instance_name_alb = condition['Values'][0]
                            rules_dict[condition['Values'][0]] = rule_arn

                    for actions in rule['Actions']:
                        if ( actions['TargetGroupArn'] != "" ):
                            taget_grp_dict[instance_name_alb] = actions['TargetGroupArn']


            for instance in instance_name_list:
                for rules_instance,arn in rules_dict.items():
                    if ( rules_instance == instance ):
                        print(rules_instance + " Has ARN " + arn )
                        ## here delete the Listener rule ARN
                        
                        response1 = client.delete_rule(
                            RuleArn=arn,
                        )
                        print(response1)
                    
                            
                    if ( rules_instance == "ia"+ instance ):
                        print(rules_instance + " Has IA ARN " + arn )
                        ## here delete the Listener rule for IA
                        
                        response2 = client.delete_rule(
                            RuleArn=arn,
                        )
                        print(response2)
                    
                        

                for target_grp_instance, target_grp_arn in taget_grp_dict.items():
                    if ( target_grp_instance == instance ):
                        print(target_grp_instance + " Has Target ARN " + target_grp_arn )

                        ## here delete the Target Grp
                        
                        response = client.delete_target_group(
                            TargetGroupArn=target_grp_arn,
                        )
                        print(response)
            print("Deleted Rules and TG")
    else:
        print("There is no instance to Terminate")
    
    if inst_cnt >= 1:  
        def delete_r53(r53_instance_name, r53_type, r53_route):
            r53_client = boto3.client("route53")
            HostedZoneId="Z0525590333MESTU5LRZJ"
            ALB_HostedZoneId="Z1H1FL5HABSF5"
            if r53_type == "MX":
                r53_client.change_resource_record_sets(
                    HostedZoneId=HostedZoneId,
                    ChangeBatch={
                        'Changes': [
                        {
                            'Action': 'DELETE',
                            'ResourceRecordSet': {
                                'Name': r53_instance_name,
                                'Type': r53_type,
                                'TTL': 300,
                                'ResourceRecords': [
                                    {
                                        'Value': r53_route
                                    }
                                ]
                            }
                        }
                    ]
                    }
                )
            else:
                r53_client.change_resource_record_sets(
                    HostedZoneId=HostedZoneId,
                    ChangeBatch={
                        'Comment': "deleting roue53 record",
                        'Changes': [
                        {
                            'Action': 'DELETE',
                            'ResourceRecordSet': {
                                'Name': r53_instance_name,
                                'Type': r53_type,
                                'AliasTarget': {
                                    'HostedZoneId': ALB_HostedZoneId,
                                    'DNSName': r53_route,
                                    'EvaluateTargetHealth': False
                                }
                            }
                        }
                    ]
                    }
                )
    else:
        print("There is no instance to Terminate")
    
    if ( inst_cnt == 0 ):
        print("No instances that matches criteria for termination")
        exit()
    else:
        print(list(dict.fromkeys(instance_id_list)))
        print(list(dict.fromkeys(instance_name_list)))
        terminate_ec2(list(dict.fromkeys(instance_id_list)))
        delete_rules_target(list(dict.fromkeys(instance_name_list)))
        for instance in list(dict.fromkeys(instance_name_list)):
            delete_r53(instance,"A","Non-PlatformLB2-1982287436.us-west-2.elb.amazonaws.com.")
            delete_r53(instance,"MX","10 mx.sendgrid.net")
            delete_r53("ia" + instance, "A", "Non-PlatformLB2-1982287436.us-west-2.elb.amazonaws.com.")

    if send_message_to_slack > 0:
        print("slck msg final", notification_message)
        send_slack_message(constant.slack_webhook_url, notification_message)
    else:
        print("Slack Message is not sent")
  
def lambda_handler(event, context):
    find_running_ec2instances()
    return {
      'statusCode': 200,
      'body': json.dumps('The Resource Termination Process is completed.')
    }
