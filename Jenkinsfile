// Purpose: LOW Severity - Unused Environment Variable
pipeline {
    agent any
    environment {
        BUILD_MODE = 'release' // ! Not used anywhere
    }
    stages {
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
    }
}
