FROM python:3.11-slim

WORKDIR /opt/dagster/app
COPY pipeline_weather/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY pipeline_weather /opt/dagster/app/pipeline_weather
EXPOSE 4000
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-m", "pipeline_weather.main"]
