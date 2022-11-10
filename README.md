# RJs College Pick'Em
## A College Football Pick'Em Style Game Selection App

RJs College Pick'Em is a game selection app where 25 games are chosen for every week of the college football season. Users select winners of those games and assign a "confidence" value to the winning team (a unique value 1-25). At the end of the game, correct selections receive a point value equal to the selected confidence - at the end of the week the user with the highest sum across the 25 games is the winner.

The application is an AWS cloud hosted web app hosted at https://rjspickem.com. The REST endpoints are defined using Python's Flask framework which communicates with an Amazon Aurora backend. The UI is designed primarily using jQuery. The whole package is built and deployed as a docker image to AWS ECS and has its traffic encrypted behind an SSL enabled load balancer. The image is hosted in dockerhub under ryanaj9393/rjscollegepickem. Additionally, the build of all infrastructure is automated via terraform. 


## Prerequisites 
- Install Python 
    - At the time of writing ```version 3.9.7``` was used
- Install HCL2 Python package
    - ```pip3 install python-hcl2```
- Install J2CLI for document templating
    - ```pip install j2cli```
- Docker Installed
    - At the time of writing ```Docker version 20.10.5, build 55c4c88``` was used 
- Terraform Installed
    At the time of writing ```Terraform v1.3.4``` was used
- Add a certificates directory at the parent level so the docker command can succeed
    - ```CMD ["flask","run","-h","0.0.0.0","-p","443","--cert=./app/certs/pickem.crt","--key=./app/certs/pickem.key"]```
    - To do so follow a guide here to create your own self-signed cert, you will need the ```openssl``` tool to do so
    - https://devopscube.com/create-self-signed-certificates-openssl/

## Build and Host Docker Image
- Build the Docker Image
    - Login - ```docker login```
    - From the directory with the ```Dockerfile``` run ```docker build -t <your_user>/<your_image_name>:<your_image_tag> .```
    - Run ```docker push <your_user>/<your_image_name>:<your_image_tag>```
    
## Deploy Resources to AWS 
- Update the Terrform variables file with your variables
    - Navigate to ```/environment/vars.tfvars```
    - Update ```aws_region```
    - Update ```existing_vpc_id```
    - Update ```existing_subnet_ids```
    - Update ```vpc_cidr```
    - Update ```domain_name```
    - Update ```dockerhub_username```
    - Update ```dockerhub_password```
    - Update ```container_name```
    - Update ```container_tag```
    - Navigate to the ```/deploy``` directory and run ```./deploy.sh```
        - This will run a ```terraform init``` -> ```terraform plan``` -> ```terraform apply``` and make sure you have a backend setup to store the state
    - After a successful apply, attempt to route to the newly deployed page to confirm its functional