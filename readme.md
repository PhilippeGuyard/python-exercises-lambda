This lambda will deploy upon push to main.

If you need to create a zip file, I have done it inside a container. For this, run the following commands:

```bash
docker build -t lambda-package .
docker run --name lambda-container lambda-package
docker cp lambda-container:/lambda_function.zip ./lambda_function.zip
rm lambda-container
```
