# aws_resource_termination
<br />

To create the lambda function <br />

-->git clone https://github.com/SharanUshurgit/instanceshutdown-.git<br />
-->cd instanceshutdown-<br />
-->pip3 install --target ./package -r requirements.txt<br />
-->cd package/<br />
-->zip -r ../instancestop.zip .<br />
-->cd ..<br />
-->zip -g instancestop.zip instanceshutdown.py <br />
-->zip -g instancestop.zip constant.py <br />
-->aws lambda create-function --function-name instance_shutdown --zip-file fileb://instancestop.zip --runtime python3.8 --role arn:aws:iam::***********:role/****** --handler instanceshutdown.lambda_handler --timeout 300<br />


To create the cloud watch triger <br />

-->aws events put-rule --name "DailyInstanceShutDown" --schedule-expression "cron(30 4,16 ? * * *)"<br />
-->aws events put-targets --rule DailyInstanceShutDown --targets "Id"="1","Arn"="arn:aws:lambda:us-west-2:***********:function:instance_shutdown"<br />


To Update the lambda

-->git clone https://github.com/UshurInc/DevOps.git<br />
-->cd devopsscripts/lambda/auto_shut_down/<br />
-->pip3 install --target ./package -r requirements.txt<br />
-->cd package/<br />
-->zip -r ../instancestop.zip .<br />
-->cd ..<br />
-->zip -g instancestop.zip instanceshutdown.py<br />
-->zip -g instancestop.zip constant.py <br />
-->aws lambda update-function-code --function-name instance_shutdown --zip-file fileb://instancestop.zip<br />
