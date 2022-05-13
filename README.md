# aws_resource_termination
<br />

To create the lambda function <br />

-->git clone https://github.com/SUTRAPUSHARANKUMARREDDY/aws_resource_termination.git<br />
-->cd aws_resource_termination<br />
-->pip3 install --target ./package -r requirements.txt<br />
-->cd package/<br />
-->zip -r ../resourcetermination.zip .<br />
-->cd ..<br />
-->zip -g resourcetermination.zip aws_resouce_termination.py <br />
-->zip -g resourcetermination.zip constant.py <br />
-->aws lambda create-function --function-name aws_resouce_termination --zip-file fileb://resourcetermination.zip --runtime python3.8 --role arn:aws:iam::***********:role/****** --handler resource_termination.lambda_handler --timeout 300 <br />


To create the cloud watch triger <br />

-->aws events put-rule --name "Daily_aws_resouce_termination" --schedule-expression "cron(30 4,16 ? * * *)"<br />
-->aws events put-targets --rule Daily_aws_resouce_termination --targets "Id"="1","Arn"="arn:aws:lambda:us-west-2:***********:function:aws_resouce_termination"<br />


To Update the lambda

-->git clone https://github.com/SUTRAPUSHARANKUMARREDDY/aws_resource_termination.git<br />
-->cd aws_resource_termination<br />
-->pip3 install --target ./package -r requirements.txt<br />
-->cd package/<br />
-->zip -r ../resourcetermination.zip .<br />
-->cd ..<br />
-->zip -g resourcetermination.zip aws_resouce_termination.py <br />
-->zip -g resourcetermination.zip constant.py <br />
-->aws lambda update-function-code --function-name aws_resouce_termination --zip-file fileb://resourcetermination.zip<br />
