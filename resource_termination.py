import boto3
import time
from datetime import datetime, timedelta
from dateutil.tz import gettz
import json
import constant

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
    notification_message = 'The following EC2 instance(s) are Terminated: \n'
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
            # there is at least one running instance in this region
            va= groups['Instances']
            for i in va:
                if 'Tags' in i:
                    dict1 = {}
                    for tag in i['Tags']:
                        dict1[tag["Key"]] = tag["Value"]
                        if ( tag["Key"] == "Name" ):
                            instance_name_tag = tag['Value']
                            print("bleble",instance_name_tag)

                        if ( tag["Key"] == "END_DATE" ):
                            end_date_str = tag['Value']

                    if end_date_str == "" or end_date_str == "NA" or end_date_str == "FOREVER":
                        print("Instance " + instance_name_tag + "not included for termination process")
                    else:
                        end_date = time.strptime(end_date_str, "%d/%m/%Y")
                        today = datetime.now(tz=gettz('Asia/Kolkata'))
                        tomorrow = today + timedelta(days=1)
                        today_str= today.strftime(format)
                        tomorrow_str = tomorrow.strftime(format)
                        today_date = time.strptime(today_str, "%d/%m/%Y")
                        tomorrow_date = time.strptime(tomorrow_str, "%d/%m/%Y")

                        #Sending reminder for instances which will get terminated next day
                        if end_date == tomorrow_date or end_date == today_date:
                            print("To be stopped tomorrow: " + instance_name_tag)
                            #send_reminder(instance_name_tag)
                        elif end_date < today_date:
                            send_message_to_slack = 1
                            if "POC" in dict1:
                                ec2_POC = dict1["POC"]
                            else:
                                ec2_POC = "No POC"
                            ec2_info = ', POC:' + ec2_POC
                            if "Name" in dict1:
                               ec2_instance_name = dict1["Name"]
                            else:
                                ec2_instance_name = "No Name"
                            ec2_info = ':point_right: , Name:' + ec2_instance_name + ec2_info
                            
                            try:
                                client.stop_instances(InstanceIds=[str(i["InstanceId"])])
                                totalinstanceshutdown += 1
                                ec2_info = ec2_info + ", InstanceId: " + i["InstanceId"]
                                ec2_info = ec2_info + ',END DATE: ' + end_date
                            except:
                                print("No Instances to ShutDown")
                            
                            notification_message += ec2_info + '\n'
                            instance_id_list.append(i['InstanceId'])
                            instance_name_list.append(instance_name_tag)
                            inst_cnt = inst_cnt + 1
    print(instance_id_list)
    print(instance_name_list)

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
    
    if ( inst_cnt == 0 ):
        print("No instances that matches criteria for termination")
        #Exit if there are no instances that matches the criteria
        exit()
    else:
        print(list(dict.fromkeys(instance_id_list)))
        print(list(dict.fromkeys(instance_name_list)))
        terminate_ec2(list(dict.fromkeys(instance_id_list)))

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
