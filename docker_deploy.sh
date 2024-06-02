#!/bin/bash

# Load environment variables
source .env

# Set variables
REGION="us-west-2"    # Example: us-east-1
PROFILE_NAME=$AWS_PROFILE   # Environment variable for AWS CLI Profile
REPO_NAME=$PROJECT_NAME  # ECR Repository Name
IMAGE_TAG=$OCR_LAMBDA_TAG   # Tag for the image

# Retrieve AWS account ID dynamically from STS
ACCOUNT_ID=$(aws sts get-caller-identity --profile $PROFILE_NAME --query "Account" --output text)

# Check if the ACCOUNT_ID was successfully retrieved
if [ -z "$ACCOUNT_ID" ]
then
    echo "Failed to retrieve AWS Account ID. Please check your AWS CLI profile and permissions."
    exit 1
fi

# AWS ECR Login
aws ecr get-login-password --region $REGION --profile $PROFILE_NAME | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build the Docker image
docker build --platform linux/amd64 -t $REPO_NAME .

# Tag the Docker image
docker tag $REPO_NAME $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG

# Push the Docker image to AWS ECR
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG

echo "Docker image pushed to AWS ECR and local images cleaned up successfully."
