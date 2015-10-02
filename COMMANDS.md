
# General commands

### List Resources
./datingnode-master resource list

### Restart a specific image
./datingnode-master ansible playbook -- playbooks/restart.yml --limit host/live-web-application-1

### Update a version number
./datingnode-master resource update --name cluster/live --set build.web_application jimmy-133


# Development commands

### Restart local development env
./datingnode-local ansible playbook -- playbooks/restart.yml

### Increment build number
./datingnode image-build-inc

### Build a local image
./datingnode image-build-web-application

### Push a local image to quay
./datingnode image-push-web-application
