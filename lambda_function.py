# Using boto 3 -> its a AWS SDK for python which helps to crate,update and delete AWS resources form our python scripts
# Boto3 makes it easy to integrate your python application,library or script with aws services including aws s3,SNS,dynamodb..

# ## Lambda funtion handler
#    1)Trigger Endpoint 
#    
#    2)Trigger SNS

import boto3
import json

sm_runtime = boto3.client('sagemaker-runtime')
sns_client = boto3.client('sns')


ENDPOINT_NAME = 'sagemaker-xgboost-2025-06-17-04-43-52-396'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-south-1:692450380298:sales-prediction-topic'

def lambda_handler(event, context):
    try:
        # Step 1: Parse JSON body from API Gateway
        body = json.loads(event['body'])
        region = body['region']
        units_sold = body['units_sold']
        unit_price = body['unit_price']

        # Step 2: Prepare CSV input for SageMaker model
        revenue_calc = units_sold * unit_price  
        input_csv = f"{region},{units_sold},{unit_price},{revenue_calc}"

        # Step 3: Invoke the SageMaker model
        response = sm_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='text/csv',
            Body=input_csv
        )

        # Step 4: Decode prediction
        prediction = float(response['Body'].read().decode('utf-8').strip())
        rounded_prediction = round(prediction, 2)

        # Step 5: Send SNS notification
        message = {
            "Region Code": region,
            "Units Sold": units_sold,
            "Unit Price": unit_price,
            "Predicted Total Revenue": rounded_prediction
        }

        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message, indent=2),
            Subject="🧠 Model Prediction Alert"
        )

        # Step 6: Return success response
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json","Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"predicted_total_revenue": rounded_prediction})
        }

    except Exception as e:
        # SNS error alert
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"🚨 Error occurred in Lambda prediction:\n{str(e)}",
            Subject="Lambda Error in Model Prediction"
        )

        return {
            "statusCode": 500,
               "headers": {
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*"
                             },
            "body": json.dumps({"error": str(e)})
        }
