#!/bin/bash

# AWS Stock Monitor Deployment Script
# This script deploys the stock monitoring application to AWS

set -e

# Configuration
STACK_NAME="stock-monitor"
ENVIRONMENT="dev"
REGION="us-east-1"
LAMBDA_FUNCTION_NAME="stock-monitor-${ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed."
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed."
        exit 1
    fi
    
    print_status "Prerequisites check passed!"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    print_status "Dependencies installed successfully!"
}

# Package Lambda function
package_lambda() {
    print_status "Packaging Lambda function..."
    
    # Create deployment package directory
    rm -rf deployment-package
    mkdir deployment-package
    
    # Copy source code
    cp -r src deployment-package/
    cp -r config deployment-package/
    
    # Install dependencies to package
    pip install -r requirements.txt -t deployment-package/
    
    # Create ZIP file
    cd deployment-package
    zip -r ../lambda-deployment-package.zip .
    cd ..
    
    print_status "Lambda function packaged successfully!"
}

# Deploy CloudFormation stack
deploy_cloudformation() {
    print_status "Deploying CloudFormation stack..."
    
    # Get user input for email addresses
    read -p "Enter sender email address (must be verified in SES): " FROM_EMAIL
    read -p "Enter recipient email address: " TO_EMAIL
    
    aws cloudformation deploy \
        --template-file infrastructure/cloudformation.yaml \
        --stack-name ${STACK_NAME}-${ENVIRONMENT} \
        --parameter-overrides \
            Environment=${ENVIRONMENT} \
            FromEmail=${FROM_EMAIL} \
            ToEmail=${TO_EMAIL} \
        --capabilities CAPABILITY_NAMED_IAM \
        --region ${REGION}
    
    print_status "CloudFormation stack deployed successfully!"
}

# Update Lambda function code
update_lambda_code() {
    print_status "Updating Lambda function code..."
    
    aws lambda update-function-code \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --zip-file fileb://lambda-deployment-package.zip \
        --region ${REGION}
    
    print_status "Lambda function code updated successfully!"
}

# Test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Invoke Lambda function
    aws lambda invoke \
        --function-name ${LAMBDA_FUNCTION_NAME} \
        --payload '{"source": "test"}' \
        --region ${REGION} \
        test-output.json
    
    # Check result
    if [ -f "test-output.json" ]; then
        print_status "Test invocation completed. Check test-output.json for results."
        cat test-output.json
        rm test-output.json
    fi
}

# Setup SES (if needed)
setup_ses() {
    print_warning "Setting up SES (Simple Email Service)..."
    print_warning "Please verify your email addresses in the AWS SES console:"
    print_warning "1. Go to AWS SES console"
    print_warning "2. Verify your sender email address"
    print_warning "3. If not in production, verify recipient email address as well"
    print_warning "4. Consider requesting production access if needed"
}

# Main deployment process
main() {
    print_status "Starting AWS Stock Monitor deployment..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                LAMBDA_FUNCTION_NAME="stock-monitor-${ENVIRONMENT}"
                shift 2
                ;;
            --region)
                REGION="$2"
                shift 2
                ;;
            --stack-name)
                STACK_NAME="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--environment ENV] [--region REGION] [--stack-name NAME]"
                echo "  --environment: Deployment environment (default: dev)"
                echo "  --region: AWS region (default: us-east-1)"
                echo "  --stack-name: CloudFormation stack name (default: stock-monitor)"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_status "Configuration:"
    print_status "  Environment: ${ENVIRONMENT}"
    print_status "  Region: ${REGION}"
    print_status "  Stack Name: ${STACK_NAME}-${ENVIRONMENT}"
    print_status "  Lambda Function: ${LAMBDA_FUNCTION_NAME}"
    
    # Run deployment steps
    check_prerequisites
    install_dependencies
    package_lambda
    deploy_cloudformation
    update_lambda_code
    test_deployment
    setup_ses
    
    print_status "🎉 Deployment completed successfully!"
    print_status "Your stock monitoring system is now running on AWS!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Verify email addresses in AWS SES console"
    print_status "2. Configure stock watchlist in config/stocks_watchlist.yaml"
    print_status "3. Adjust analysis parameters in config/config.yaml"
    print_status "4. Monitor CloudWatch logs for execution results"
    
    # Cleanup
    rm -f lambda-deployment-package.zip
    rm -rf deployment-package
}

# Run main function
main "$@"
