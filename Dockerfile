FROM apache/airflow

WORKDIR /app

# Install necessary system packages for building Python packages
USER root
RUN apt-get update

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"    

# Copy project files
COPY . /app/

# Install dependencies
RUN poetry install

USER airflow
