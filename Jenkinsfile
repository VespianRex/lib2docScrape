pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        VENV_PATH = '.venv'
        REPORTS_DIR = 'reports'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 45, unit: 'MINUTES')
        timestamps()
    }
    
    triggers {
        // Run daily at 2 AM
        cron('0 2 * * *')
        // Run on SCM changes
        pollSCM('H/5 * * * *')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.BUILD_TIMESTAMP = sh(
                        script: 'date +%Y%m%d_%H%M%S',
                        returnStdout: true
                    ).trim()
                }
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    # Install UV if not present
                    if ! command -v uv &> /dev/null; then
                        curl -LsSf https://astral.sh/uv/install.sh | sh
                        export PATH="$HOME/.cargo/bin:$PATH"
                    fi
                    
                    # Create virtual environment
                    uv venv ${VENV_PATH}
                    
                    # Activate and install dependencies
                    . ${VENV_PATH}/bin/activate
                    uv pip install -e .
                    uv pip install pytest pytest-asyncio pytest-timeout pytest-html pytest-cov psutil
                '''
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        sh '''
                            . ${VENV_PATH}/bin/activate
                            uv pip install ruff
                            ruff check src/ tests/ --output-format=junit > ${REPORTS_DIR}/ruff-report.xml || true
                        '''
                    }
                }
                
                stage('Type Checking') {
                    steps {
                        sh '''
                            . ${VENV_PATH}/bin/activate
                            uv pip install mypy
                            mypy src/ --junit-xml ${REPORTS_DIR}/mypy-report.xml || true
                        '''
                    }
                }
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    mkdir -p ${REPORTS_DIR}
                    
                    python -m pytest tests/ \
                        -m "not slow and not real_world and not performance" \
                        --timeout=30 \
                        --junit-xml=${REPORTS_DIR}/junit-unit.xml \
                        --cov=src \
                        --cov-report=xml:${REPORTS_DIR}/coverage-unit.xml \
                        --cov-report=html:${REPORTS_DIR}/htmlcov-unit \
                        --html=${REPORTS_DIR}/unit-report.html \
                        --self-contained-html \
                        -v
                '''
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    
                    python scripts/run_e2e_tests.py \
                        --timeout=90 \
                        --skip-performance \
                        --report=${REPORTS_DIR}/e2e-integration-${BUILD_TIMESTAMP}.json \
                        --junit-xml=${REPORTS_DIR}/junit-integration.xml \
                        --html-report=${REPORTS_DIR}/integration-report.html \
                        --coverage
                '''
            }
        }
        
        stage('Library Documentation Tests') {
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    
                    # Run our custom library documentation scraping tests
                    python scripts/test_project_dependencies.py \
                        --output=${REPORTS_DIR}/dependency-docs-${BUILD_TIMESTAMP}.json \
                        --html-report=${REPORTS_DIR}/dependency-report.html \
                        --timeout=120
                '''
            }
        }
        
        stage('Performance Benchmarks') {
            when {
                anyOf {
                    branch 'main'
                    triggeredBy 'TimerTrigger'
                }
            }
            steps {
                sh '''
                    . ${VENV_PATH}/bin/activate
                    
                    python scripts/run_e2e_tests.py \
                        --performance-only \
                        --timeout=180 \
                        --report=${REPORTS_DIR}/performance-${BUILD_TIMESTAMP}.json \
                        --junit-xml=${REPORTS_DIR}/junit-performance.xml \
                        --html-report=${REPORTS_DIR}/performance-report.html
                '''
            }
        }
    }
    
    post {
        always {
            // Archive test reports
            archiveArtifacts artifacts: 'reports/**/*', fingerprint: true
            
            // Publish test results
            publishTestResults testResultsPattern: 'reports/junit-*.xml'
            
            // Publish HTML reports
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'reports',
                reportFiles: '*.html',
                reportName: 'Test Reports'
            ])
            
            // Publish coverage
            publishCoverage adapters: [
                coberturaAdapter('reports/coverage-*.xml')
            ], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
        }
        
        success {
            echo 'Pipeline completed successfully!'
            
            // Send notification (configure as needed)
            // emailext (
            //     subject: "✅ Build Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
            //     body: "Build completed successfully. View reports: ${env.BUILD_URL}",
            //     to: "${env.CHANGE_AUTHOR_EMAIL}"
            // )
        }
        
        failure {
            echo 'Pipeline failed!'
            
            // Send failure notification
            // emailext (
            //     subject: "❌ Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
            //     body: "Build failed. Check logs: ${env.BUILD_URL}console",
            //     to: "${env.CHANGE_AUTHOR_EMAIL}"
            // )
        }
        
        unstable {
            echo 'Pipeline completed with warnings!'
        }
        
        cleanup {
            // Clean up workspace if needed
            sh 'rm -rf ${VENV_PATH} || true'
        }
    }
}
