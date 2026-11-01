My Azure project execution
-----------------------------------
1. Import git repo in azure repo
Git repo: https://github.com/Sachin-dev-hub/test.git

2. created a agent in default agent pool(create new) in azure project setting
Agent for linux
~/$ mkdir myagent && cd myagent
~/myagent$ tar zxvf ~/Downloads/vsts-agent-linux-x64-5.281.1.tar.gz
"C:\Users\sachin_maskar\Downloads\vsts-agent-linux-x64-5.281.1.tar.gz"

dragged and dropped downloaded tar file in linux VM environment or download using wget command
extract it in linux 
tar zxvf /home/sachin/Downloads/vsts-agent-linux-x64-5.281.1.tar.gz
useradd -m -s /bin/bash azureagent

mv /root/myagent /home/azureagent/
chown -R azureagent:azureagent /home/azureagent/myagent
su - azureagent
cd /home/azureagent/myagent
./config.sh
Y
server URL: https://dev.azure.com/SachinEnterprise

> delete this token once work done from the azure

Enter authentication type (press enter for PAT) >
Enter personal access token > ************************************************************************************
Connecting to server ...

>> Register Agent:

Enter agent pool (press enter for default) >  // enter becuas agent pool is default
Enter agent name (press enter for worker01) > azureagent   // node agent/user is entered
Scanning for tool capabilities.
Connecting to the server.
Successfully added the agent
Testing agent connection.
Enter work folder (press enter for _work) >  // Enter
2026-11-01 13:36:32Z: Settings Saved.
azureagent@worker01:~/myagent$
// Agent is offline in azure agent
azureagent@worker01:~/myagent$ chmod 777 run.sh >> do not give full permsssion
azureagent@worker01:~/myagent$ ./run.sh
Scanning for tool capabilities.
Connecting to the server.
2026-11-01 13:43:27Z: Listening for Jobs
// docker should be installed on the agent.
// grand permission to the azure user to the run docker demon
azureuser > defalt user
roor# usermod -aG docker azureagent
root$# su azureagent
> start agent
./run.sh

// Keep user running, you will see the logs if you pipeline get triggered.

---------------------------------------------
Azure Devops
---------------------------
1. crete new pipeline > select azure repo> >select your repo > docker > validate and configure > create/ add pipeline > save
2. do chagnes in repo: app
3. check pipeline is running or not
-----------------------------------------




