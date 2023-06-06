
# Import necessary modules from the Airflow library
from datetime import timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from docker.types import Mount


# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',  # Owner of the DAG
    'description': 'DAG to run Docker containers',  # Description of the DAG
    'depend_on_past': False,  # The DAG does not have dependencies on past runs
    'start_date': days_ago(2),  # Start date of the DAG
    'email_on_failure': False,  # Do not email on failure
    'email_on_retry': False,  # Do not email on retry
    'retries': 1,  # Number of retries if the task fails
    'retry_delay': timedelta(minutes=5),  # Delay between retries
}

# Define the DAG
dag = DAG(
    'docker_dag',  # Name of the DAG
    default_args=default_args,  # Default arguments for the DAG
    schedule_interval=timedelta(minutes=10),  # Schedule interval for the DAG
)

# Define the first task
t1 = DockerOperator(
    task_id='extract_satellite_image',  # Unique identifier for the task
    image='test-notebook-app',  # Name of the Docker image to run
    api_version='auto',  # API version to use
    auto_remove=True,  # Automatically remove the Docker container when it exits
    command="/bin/bash -c 'python /app/extract_satellite_image.py'",  # Command to run in the Docker container
    docker_url="unix://var/run/docker.sock",  # URL of the Docker daemon
    network_mode="bridge",  # Network mode for the Docker container
    mounts=[Mount(target='/app', source='shared_volume', type='volume')],# 'mounts' is a list of Mount objects. Each Mount object represents a volume to be mounted in the Docker container.
    # The Mount object's 'target' argument is the path in the Docker container where the volume will be mounted.
    # The 'source' argument is the name of the Docker volume to mount.
    # The 'type' argument is the type of the mount, which is 'volume' in this case.
    dag=dag,  # DAG that the task belongs to
)

# Define the second task
t2 = DockerOperator(
    task_id='calculate_ndvi',  # Unique identifier for the task
    image='test-notebook-app',  # Name of the Docker image to run
    api_version='auto',  # API version to use
    auto_remove=True,  # Automatically remove the Docker container when it exits
    command="/bin/bash -c 'python /app/calculate_ndvi.py'",  # Command to run in the Docker container
    docker_url="unix://var/run/docker.sock",  # URL of the Docker daemon
    network_mode="bridge",  # Network mode for the Docker container
    mounts=[Mount(target='/app', source='shared_volume', type='volume')],# Similarly, for the second task, we're also mounting the 'shared_volume' Docker volume to the '/app' directory in the container.
    # This means that the 'dataset.nc' file written by the first task will be available to the second task.
    dag=dag,  # DAG that the task belongs to
)

# Define the order of the tasks
t1 >> t2  # t2 depends on t1; t1 must complete successfully before t2 starts
