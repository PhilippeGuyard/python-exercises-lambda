from lambda_function import lambda_handler

event = {}
context = {}

# Invoke the lambda_handler function
response = lambda_handler(event, context)
print(response)
