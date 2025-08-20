// Purpose: MEDIUM Severity - Dangerous Shell Usage
pipeline {
    agent any
    stages {
        stage('Deploy') {
            steps {
                sh 'curl -X POST http://insecure-service.local/deploy'
            }
        }
    }
}
