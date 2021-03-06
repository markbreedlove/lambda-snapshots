# Lambda Snapshots

Python module with AWS Lambda functions to make EBS volume snapshots and
delete old ones.

See http://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html

To create `.zip` file for uploading:
```
$ cd lambda-snapshots
$ zip -r lamdbda-snapshots.zip . -x .git\*
```
Then upload that zipfile when you create your Lambda function.

Create separate Lambda functions for backup and delete, but upload the same
zipfile. When you create your function, use the appropriate function name
for the `Handler` property.  For example, I have a Lambda function named
`make_snapshots` and its Handler is `snapshots.make_snapshots` because
`snapshots.py` is the `snapshots` module and `make_snapshots` is the function
that I want.

For the `logging` calls to work, you will need an IAM policy that grants
CloudWatch write privileges to be assigned to the role under which the Lambda
job runs.  Here is an example:
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "your-unique-ID-here",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:*:*:*"
            ]
        }
    ]
}
```