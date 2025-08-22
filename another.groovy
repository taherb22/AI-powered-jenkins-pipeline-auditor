// Purpose: HIGH Severity - Hardcoded Secrets
pipeline {
    agent any
    environment {
        AWS_SECRET_KEY = 'AKIAIOSFODNN7EXAMPLE'
    }
    stages {
        stage('Deploy') {
            steps {
                sh 'aws deploy --key $AWS_SECRET_KEY'
            }
        }
    }
}
