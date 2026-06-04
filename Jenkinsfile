pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        CONFIG_REPO_URL = 'https://github.com/ovejabalvin/todo-list-aws-config.git'
        AWS_REGION = 'us-east-1'
    }

    stages {
        stage('Resolve Branch') {
            steps {
                script {
                    if (env.BRANCH_NAME == 'develop') {
                        env.TARGET_ENV = 'staging'
                        env.CONFIG_BRANCH = 'staging'
                        env.SAM_ENV = 'staging'
                        env.STACK_NAME = 'todo-list-aws-staging'
                        env.INTEGRATION_TEST = 'test/integration/todoApiTest.py'
                        env.JUNIT_FILE = 'reports/pytest-integration.xml'
                        env.TEST_LOG = 'reports/pytest-integration.log'
                    } else if (env.BRANCH_NAME == 'master') {
                        env.TARGET_ENV = 'production'
                        env.CONFIG_BRANCH = 'production'
                        env.SAM_ENV = 'production'
                        env.STACK_NAME = 'todo-list-aws-production'
                        env.INTEGRATION_TEST = 'test/integration/todoApiReadOnlyTest.py'
                        env.JUNIT_FILE = 'reports/pytest-read-only.xml'
                        env.TEST_LOG = 'reports/pytest-read-only.log'
                    } else {
                        error "Esta practica solo ejecuta ramas develop y master. Rama actual: ${env.BRANCH_NAME}"
                    }
                }
                sh '''
                    set -eu
                    echo "BRANCH_NAME=$BRANCH_NAME"
                    echo "TARGET_ENV=$TARGET_ENV"
                    echo "Nodo Resolve Branch: $(hostname)"
                    echo "Usuario Resolve Branch: $(whoami)"
                '''
            }
        }

        stage('Get Code') {
            steps {
                checkout scm
                sh '''
                    set -eu
                    rm -rf .cp-config reports
                    mkdir -p reports
                    git clone --depth 1 --branch "$CONFIG_BRANCH" "$CONFIG_REPO_URL" .cp-config
                    cp .cp-config/samconfig.toml samconfig.toml
                    test -f samconfig.toml
                    echo "Codigo: $BRANCH_NAME" | tee reports/pipeline-context.txt
                    echo "Config: $CONFIG_BRANCH" | tee -a reports/pipeline-context.txt
                    echo "Nodo Get Code: $(hostname)" | tee -a reports/pipeline-context.txt
                    echo "Usuario Get Code: $(whoami)" | tee -a reports/pipeline-context.txt
                '''
            }
        }

        stage('Install Tools') {
            steps {
                sh '''
                    set -eu
                    rm -rf .venv
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip
                    python -m pip install -r requirements-dev.txt
                    python -m pip install -r src/requirements.txt
                '''
            }
        }

        stage('Static Test') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    set -eu
                    . .venv/bin/activate
                    mkdir -p reports
                    flake8 src --count --statistics --output-file=reports/flake8.txt || true
                    bandit -r src -f txt -o reports/bandit.txt || true
                    bandit -r src -f html -o reports/bandit.html || true
                    test -f reports/flake8.txt
                    test -f reports/bandit.txt
                    test -f reports/bandit.html
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/flake8.txt,reports/bandit.txt,reports/bandit.html', allowEmptyArchive: true
                }
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    set -eu
                    sam validate --region "$AWS_REGION"
                    sam build
                    sam deploy --config-env "$SAM_ENV" --no-confirm-changeset --no-fail-on-empty-changeset

                    aws cloudformation describe-stacks \
                        --stack-name "$STACK_NAME" \
                        --region "$AWS_REGION" \
                        --output json > reports/stack.json

                    python - <<'PY'
import json

with open("reports/stack.json") as f:
    data = json.load(f)

outputs = data["Stacks"][0].get("Outputs", [])
for output in outputs:
    if output.get("OutputKey") == "BaseUrlApi":
        with open("reports/base_url.txt", "w") as f:
            f.write(output["OutputValue"] + "\\n")
        break
else:
    raise SystemExit("No se encontro el output BaseUrlApi")
PY

                    cat reports/base_url.txt
                    test -s reports/base_url.txt
                '''
            }
        }

        stage('Rest Test') {
            steps {
                sh '''
                    set -eu
                    . .venv/bin/activate
                    export BASE_URL="$(cat reports/base_url.txt)"
                    echo "BASE_URL=$BASE_URL"
                    set +e
                    pytest -q "$INTEGRATION_TEST" --junitxml="$JUNIT_FILE" > "$TEST_LOG" 2>&1
                    status=$?
                    set -e
                    cat "$TEST_LOG"
                    exit $status
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/*.xml'
                    archiveArtifacts artifacts: 'reports/pytest-*', allowEmptyArchive: true
                }
            }
        }

        stage('Promote') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    set -eu
                    git config user.email "jenkins@example.local"
                    git config user.name "Jenkins CI"
                    git fetch origin master develop
                    git checkout master
                    git merge --no-edit origin/develop
                    git push origin master
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
        }
    }
}