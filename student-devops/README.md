# Student Registration DevOps Project

A hands-on project for Sachin: browser UI -> Flask/Gunicorn API -> PostgreSQL.
Features: add/list/edit/delete students, unique email checks, input validation,
parameterized SQL, persistent database, logs, independent liveness and database
readiness checks, resource limits, Docker Compose, kind Kubernetes, Jenkins.

This is a working application starter for a production-style lab, not a complete
production product. No authentication, authorization, HTTPS, migrations framework,
HA database, or backup scheduling is included. Keep it private and use fictional
student data. PostgreSQL uses a single lab user (also an administrator); a real
service should separate database owner/migration and restricted application roles.
Dependency versions are pinned for reproducibility, not certified vulnerability-free.

## 1. Before starting (escbash terminal)

    docker --version
    docker compose version
    kind get clusters
    kubectl config current-context
    kubectl get nodes
    kubectl get storageclass
    free -h

Commands assume your kind cluster name is `kind`. Substitute the name shown by
`kind get clusters` if different. Stay in this project's directory. Do not recreate
or delete your existing cluster. A default StorageClass is required for the PVC;
if none is marked `(default)`, stop and share the storageclass output.

## 2. Build and test locally with Docker Compose

Create a random local database password (requires python3):

    python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_hex(24))" > .env
    chmod 600 .env
    docker compose up -d --build
    docker compose ps
    docker compose logs --tail=50 app db
    curl -f http://127.0.0.1:8080/health/ready

The image `sachinmaskar/student-registration:v2` is built on YOUR machine; it has
not yet been uploaded to Docker Hub. Your previous v1 image is not changed.
Compose uses localhost only. Test the API even if the remote browser cannot reach it:

    curl -f -X POST http://127.0.0.1:8080/api/students -H 'Content-Type: application/json' -d '{"name":"Demo Student","email":"demo@example.com","course":"DevOps"}'
    curl -f http://127.0.0.1:8080/api/students

Run this POST only once per email. A repeat should return 409.
Stop Compose before Kubernetes access to free host port 8080:

    docker compose down

The named Compose volume persists. Do not add `-v`: that removes its database.
Compose and Kubernetes use SEPARATE database volumes; the demo record above will
not automatically appear in Kubernetes.

## 3. Deploy on the existing kind cluster

    kind load docker-image sachinmaskar/student-registration:v2 --name kind
    kubectl create namespace student-devops

Create a local password file for the Kubernetes Secret without displaying it:

    python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_hex(24))" > .env
    chmod 600 .env
    kubectl -n student-devops create secret generic database-secret --from-env-file=.env
    kubectl apply -f k8s/database.yaml
    kubectl -n student-devops rollout status statefulset/student-db --timeout=180s
    kubectl -n student-devops get pvc
    kubectl apply -f k8s/application.yaml
    kubectl -n student-devops rollout status deployment/student-app --timeout=180s
    kubectl -n student-devops get pods,svc,pvc

Namespace/Secret creation is a first-time step. If already present, reuse them.
Do not regenerate the Secret password for an existing database volume: PostgreSQL
only applies its initialization password and init SQL on the first empty-volume
startup. Changing a Kubernetes Secret alone does not change a database password.
Init SQL creates the schema on first startup; future schema changes need explicit
migration scripts, not edits to this init file.

## 4. Open the application

    kubectl -n student-devops port-forward --address 0.0.0.0 svc/student-app 8080:80

Keep this terminal running. In a SECOND terminal:

    curl -f http://127.0.0.1:8080/health/ready
    curl -f http://127.0.0.1:8080/api/students

Use escbash's port preview/open-port feature for port 8080 (HTTP backend).
Use the URL escbash gives you; its proxy may expose an HTTPS browser URL.
Binding 0.0.0.0 makes this port reachable on the lab host interfaces; use only
private/controlled lab access. If no port preview is available, continue with curl.
This is temporary lab access; stable ingress/HTTPS is a later stage.

## 5. Verify real database persistence

Add a fictional student through the browser or curl. Then:

    kubectl -n student-devops rollout restart deployment/student-app
    kubectl -n student-devops rollout status deployment/student-app

Restart port-forward if it disconnects. The record should remain. Then test a
database Pod replacement:

    kubectl -n student-devops delete pod student-db-0
    kubectl -n student-devops rollout status statefulset/student-db --timeout=180s

Records should remain because of the PVC. This protects against Pod replacement,
not cluster deletion, lost host storage, or expired escbash sessions. Export backups.

## 6. Scale and troubleshoot

    kubectl -n student-devops scale deployment/student-app --replicas=2
    kubectl -n student-devops get pods
    kubectl -n student-devops logs deployment/student-app --tail=50
    kubectl -n student-devops get events --sort-by=.metadata.creationTimestamp

Both application Pods use the same database. Two Pods on one node do not provide
node-level high availability. Port-forward targets one Pod, so it is not a
load-balancing test. Use one replica again if host memory is tight.

Common problems:
- ImagePullBackOff: verify the local image was loaded into the correct kind cluster.
- PVC Pending: inspect the default StorageClass and `kubectl describe pvc`.
- CrashLoopBackOff: inspect logs and `kubectl logs POD --previous`.
- App not Ready: inspect `/health/ready`, DB logs, Secret, and DB service endpoints.
- Pods Pending: use `kubectl describe pod POD` for resources or taints. Do not
  remove all taints blindly.

## 7. Backup and restore

Backup to the escbash host, then download it somewhere durable:

    kubectl -n student-devops exec student-db-0 -- pg_dump -U studentapp -d students > students-backup.sql

Restore only into a separate EMPTY test database, to avoid overwriting records:

    kubectl -n student-devops exec student-db-0 -- createdb -U studentapp students_restore
    kubectl -n student-devops exec -i student-db-0 -- psql -v ON_ERROR_STOP=1 -U studentapp -d students_restore < students-backup.sql
    kubectl -n student-devops exec student-db-0 -- psql -U studentapp -d students_restore -c 'SELECT count(*) FROM students;'

Check restored rows against the source. Backups can contain personal data; do not
commit them to GitHub. This is a manual backup exercise, not automated recovery.

## 8. Push your image to Docker Hub

Create/use repository `sachinmaskar/student-registration`, log in with a Docker Hub
access token when prompted, then push:

    docker login -u sachinmaskar
    docker push sachinmaskar/student-registration:v2

Do not paste the token into code or Git. If repository is private, configure an
imagePullSecret before using it in Kubernetes. Jenkins instructions below assume
public images. No registry upload has been performed by the project author.

## 9. Jenkins (after manual deployment works)

Commit this project to your own GitHub repository. Configure a Jenkins Pipeline
from SCM using the supplied Jenkinsfile. The Jenkins agent needs python3 + venv,
Docker CLI/daemon access, kubectl, and network access to the kind API. A Jenkins
container often cannot use the host's localhost kubeconfig endpoint directly;
start with a Jenkins agent running on the same escbash host as kind.

Create Jenkins credentials:
- `dockerhub`: username/password type, Docker Hub username + access token.
- `kind-kubeconfig`: secret file, kubeconfig usable from the Jenkins agent.

Use a namespace-restricted deployment identity for a shared Jenkins installation;
do not upload your cluster-admin kubeconfig to a shared CI service. Credential
configuration and agent reachability need validating in your actual environment.
Database/Secret setup is manual and happens before the pipeline. Pipeline stages:
checkout -> unit tests -> Docker build -> push immutable build-number tag ->
update existing Deployment -> wait for rollout/readiness. A new Jenkins job may
reuse build numbers, so use a Git SHA tag before sharing the registry across jobs.

Pipeline failure does NOT automatically roll back. Inspect the failure, then:

    kubectl -n student-devops rollout history deployment/student-app
    kubectl -n student-devops rollout undo deployment/student-app
    kubectl -n student-devops rollout status deployment/student-app --timeout=180s

Rollback requires a previous revision and an accessible previous image. It rolls
back the Pod template, not PostgreSQL data or database schema.

## 10. Next extensions

Add Prometheus/Grafana only after checking available RAM. Cluster resource
monitoring and application business metrics are separate: this app does not yet
expose `/metrics`. Later add login/roles, TLS ingress, restricted DB roles, explicit
schema migrations, scheduled backups, image scanning, and a CI integration test
against a disposable PostgreSQL service.

## Code checks

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
    .venv/bin/python -m unittest discover -s tests -v

Tests cover validation, invalid requests, UI response, independent liveness, and
readiness during database failure. CRUD + real database behavior must be verified
with the Compose/Kubernetes steps above.
