# AWS Stock Monitor Deployment Script for Windows PowerShell
# This script deploys the stock monitoring application to AWS

param(
    [string]$Environment = "dev",
    [string]$Region = "us-east-1",
    [string]$StackName = "stock-monitor",
    [switch]$Help
)

# Configuration
$LambdaFunctionName = "stock-monitor-$Environment"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Show help
if ($Help) {
    Write-Host "Usage: .\deploy.ps1 [-Environment ENV] [-Region REGION] [-StackName NAME]"
    Write-Host "  -Environment: Deployment environment (default: dev)"
    Write-Host "  -Region: AWS region (default: us-east-1)"
    Write-Host "  -StackName: CloudFormation stack name (default: stock-monitor)"
    Write-Host "  -Help: Show this help message"
    exit 0
}

# Check prerequisites
function Test-Prerequisites {
    Write-Status "Checking prerequisites..."
    
    # Check AWS CLI
    try {
        aws --version | Out-Null
    }
    catch {
        Write-Error "AWS CLI is not installed. Please install it first."
        exit 1
    }
    
    # Check AWS credentials
    try {
        aws sts get-caller-identity | Out-Null
    }
    catch {
        Write-Error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    }
    
    # Check Python
    try {
        python --version | Out-Null
    }
    catch {
        Write-Error "Python is not installed."
        exit 1
    }
    
    # Check pip
    try {
        pip --version | Out-Null
    }
    catch {
        Write-Error "pip is not installed."
        exit 1
    }
    
    Write-Status "Prerequisites check passed!"
}

# Install Python dependencies
function Install-Dependencies {
    Write-Status "Installing Python dependencies..."
    
    if (!(Test-Path "venv")) {
        python -m venv venv
    }
    
    # Activate virtual environment
    & ".\venv\Scripts\Activate.ps1"
    
    pip install -r requirements.txt
    
    Write-Status "Dependencies installed successfully!"
}

# Package Lambda function
function New-LambdaPackage {
    Write-Status "Packaging Lambda function..."
    
    # Create deployment package directory
    if (Test-Path "deployment-package") {
        Remove-Item "deployment-package" -Recurse -Force
    }
    New-Item -ItemType Directory -Name "deployment-package" | Out-Null
    
    # Copy source code
    Copy-Item "src" "deployment-package\" -Recurse
    Copy-Item "config" "deployment-package\" -Recurse
    
    # Install dependencies to package
    pip install -r requirements.txt -t "deployment-package\"
    
    # Create ZIP file
    Set-Location "deployment-package"
    Compress-Archive -Path "*" -DestinationPath "..\lambda-deployment-package.zip" -Force
    Set-Location ".."
    
    Write-Status "Lambda function packaged successfully!"
}

# Deploy CloudFormation stack
function Deploy-CloudFormation {
    Write-Status "Deploying CloudFormation stack..."
    
    # Get user input for email addresses
    $FromEmail = Read-Host "Enter sender email address (must be verified in SES)"
    $ToEmail = Read-Host "Enter recipient email address"
    
    aws cloudformation deploy `
        --template-file "infrastructure\cloudformation.yaml" `
        --stack-name "$StackName-$Environment" `
        --parameter-overrides `
            "Environment=$Environment" `
            "FromEmail=$FromEmail" `
            "ToEmail=$ToEmail" `
        --capabilities CAPABILITY_NAMED_IAM `
        --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "CloudFormation stack deployed successfully!"
    } else {
        Write-Error "Failed to deploy CloudFormation stack"
        exit 1
    }
}

# Update Lambda function code
function Update-LambdaCode {
    Write-Status "Updating Lambda function code..."
    
    aws lambda update-function-code `
        --function-name $LambdaFunctionName `
        --zip-file "fileb://lambda-deployment-package.zip" `
        --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Lambda function code updated successfully!"
    } else {
        Write-Error "Failed to update Lambda function code"
        exit 1
    }
}

# Test deployment
function Test-Deployment {
    Write-Status "Testing deployment..."
    
    # Invoke Lambda function
    aws lambda invoke `
        --function-name $LambdaFunctionName `
        --payload '{\"source\": \"test\"}' `
        --region $Region `
        "test-output.json"
    
    # Check result
    if (Test-Path "test-output.json") {
        Write-Status "Test invocation completed. Check test-output.json for results."
        Get-Content "test-output.json"
        Remove-Item "test-output.json"
    }
}

# Setup SES information
function Show-SESSetup {
    Write-Warning "Setting up SES (Simple Email Service)..."
    Write-Warning "Please verify your email addresses in the AWS SES console:"
    Write-Warning "1. Go to AWS SES console"
    Write-Warning "2. Verify your sender email address"
    Write-Warning "3. If not in production, verify recipient email address as well"
    Write-Warning "4. Consider requesting production access if needed"
}

# Main deployment process
function Main {
    Write-Status "Starting AWS Stock Monitor deployment..."
    
    Write-Status "Configuration:"
    Write-Status "  Environment: $Environment"
    Write-Status "  Region: $Region"
    Write-Status "  Stack Name: $StackName-$Environment"
    Write-Status "  Lambda Function: $LambdaFunctionName"
    
    try {
        # Run deployment steps
        Test-Prerequisites
        Install-Dependencies
        New-LambdaPackage
        Deploy-CloudFormation
        Update-LambdaCode
        Test-Deployment
        Show-SESSetup
        
        Write-Status "🎉 Deployment completed successfully!"
        Write-Status "Your stock monitoring system is now running on AWS!"
        Write-Status ""
        Write-Status "Next steps:"
        Write-Status "1. Verify email addresses in AWS SES console"
        Write-Status "2. Configure stock watchlist in config/stocks_watchlist.yaml"
        Write-Status "3. Adjust analysis parameters in config/config.yaml"
        Write-Status "4. Monitor CloudWatch logs for execution results"
    }
    catch {
        Write-Error "Deployment failed: $($_.Exception.Message)"
        exit 1
    }
    finally {
        # Cleanup
        if (Test-Path "lambda-deployment-package.zip") {
            Remove-Item "lambda-deployment-package.zip"
        }
        if (Test-Path "deployment-package") {
            Remove-Item "deployment-package" -Recurse -Force
        }
    }
}

# Run main function
Main
