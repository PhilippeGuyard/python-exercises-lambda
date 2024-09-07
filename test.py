from lambda_function import lambda_handler

# Create the event dictionary that matches the Lambda proxy integration structure
event = {}

# Simulate the AWS Lambda context (can be an empty dictionary for testing)
context = {}

# Invoke the lambda_handler function
response = lambda_handler(event, context)
print(response)
