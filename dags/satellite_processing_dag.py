# Author: Suresh Andem
# Date: June5, 2023
# Last Updated: Suresh Andem
# Last Updated Date: June 6, 2023

# Import the required modules
from datetime import timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from docker.types import Mount


# Define the default arguments for the Directed Acyclic Graph (DAG)
default_args = {
    'owner': 'airflow', # owner of the task
    'description': 'DAG to run Docker containers',  # a brief description of the task
    'depend_on_past': False, # task does not depend on past runs
    'start_date': days_ago(1), # tasks are backdated and started a day ago
    'email_on_failure': False,   # no email is sent if the task fails
    'email_on_retry': False, # no email is sent if the task retries
    'retries': 1, # task will be retried once if it fails
    'retry_delay': timedelta(minutes=5), # delay between retries will be 5 minutes
}
# Define the DAG
dag = DAG(
    'satellite_processing_dag', # unique identifier for the DAG
    default_args=default_args, # applying the default arguments
    schedule_interval=timedelta(minutes=10), # the DAG will run every 10 minutes
)
# Define the first DockerOperator task (t1) to run the SQS script in a Docker container
t1 = DockerOperator(
    task_id='sqs_script',
    image='sqs-app',  # Docker Image ID
    api_version='auto',
    auto_remove=True,
    command="/bin/bash -c 'python3 /app/sqs_script.py --queue_name satellite_image_processing_queue --aoi \"POLYGON((-75.91505153891599 5.061461711492797,-75.9102450203613 5.061461711492797,-75.9102450203613 5.057870869400911,-75.91505153891599 5.057870869400911,-75.91505153891599 5.061461711492797))\"'",
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[Mount(target='/root/.aws', source='/root/.aws', type='bind', read_only=True)],
    dag=dag, # specifying the DAG to which the task belongs
)
# Define the second DockerOperator task (t2) to extract the satellite image
t2 = DockerOperator(
    task_id='extract_satellite_image',
    image='sqs-app',
    api_version='auto',
    auto_remove=True,
    command="/bin/bash -c 'python3 /app/extract_satellite_image.py --aoi \"POLYGON((-75.91505153891599 5.061461711492797,-75.9102450203613 5.061461711492797,-75.9102450203613 5.057870869400911,-75.91505153891599 5.057870869400911,-75.91505153891599 5.061461711492797))\" --file_path /app/output/dataset.nc'",
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
     mounts=[
        Mount(target='/root/.aws', source='/root/.aws', type='bind', read_only=True),
        Mount(target='/app/output', source='/root/Airflow_Docker/airflow_scripts/sqs', type='bind')
    ],
    dag=dag, # specifying the DAG to which the task belongs
)

# Define the third DockerOperator task (t3) to calculate the NDVI
t3 = DockerOperator(
    task_id='calculate_ndvi',
    image='sqs-app',
    api_version='auto',
    auto_remove=True,
    command="/bin/bash -c 'python3 /app/calculate_ndvi.py --input_file_path /app/output/dataset.nc --output_file_path /app/output/ndvi_dataset.nc'",
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[
        Mount(target='/root/.aws', source='/root/.aws', type='bind', read_only=True),
        Mount(target='/app/output', source='/root/Airflow_Docker/airflow_scripts/sqs', type='bind')
    ],
    dag=dag, # specifying the DAG to which the task belongs
)


# Define the order of the tasks - sqs_script (t1) runs first, 
# then extract_satellite_image (t2), and finally calculate_ndvi (t3)
t1 >> t2 >> t3
