# Use the AWS Lambda Python runtime as a parent image
FROM public.ecr.aws/lambda/python:3.10

# Set environment variables for poetry and Python path
ENV POETRY_VERSION=1.4.0 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH="${PYTHONPATH}:${LAMBDA_TASK_ROOT}"

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy only the necessary dependency files
WORKDIR ${LAMBDA_TASK_ROOT}
COPY pyproject.toml poetry.lock ./

# Install Python dependencies without dev dependencies and cleanup in the same layer
RUN poetry install --no-dev --no-root --no-ansi --no-interaction && \
    rm -rf /root/.cache/pypoetry

# Copy the rest of the application
COPY src ./

# You may specify your handler in CDK or through AWS Console
CMD ["overwritten in components"]