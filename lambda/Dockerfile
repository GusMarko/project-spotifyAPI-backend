FROM public.ecr.aws/lambda/python:3.11


WORKDIR /var/task


COPY requirements.txt .


RUN pip install -r requirements.txt


COPY artists_data.py .


CMD ["artists_data.lambda_handler"]