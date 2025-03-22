FROM public.ecr.aws/lambda/python:3.11


WORKDIR /var/task


COPY requirements.txt .


RUN pip install -r requirements.txt


COPY lambda_handler.py .


CMD ["artist_data.lambda_handler"]