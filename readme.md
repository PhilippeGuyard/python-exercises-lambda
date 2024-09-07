This lambda will deploy upon push to main.

If you need to create a zip file, I have done it inside a container. For this, run the following commands:

```bash
docker build -t lambda-package .
docker run --name lambda-container lambda-package
docker cp lambda-container:/lambda_function.zip ./lambda_function.zip
rm lambda-container
```

for a detailed walk-through, see here:
https://philippe-guyard.notion.site/Use-OpenAI-to-send-daily-Python-exercises-via-email-8ca45ac8f1aa45688f48477cf19619c2
