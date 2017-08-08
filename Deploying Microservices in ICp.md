# Deploying a Microservice application in IBM Cloud private

This tutorial shows you how to deploy a Microservice application in IBM Cloud private.
We will use the BlueCompute application as an example of a Microservice application.
For more information on BlueCompute, she the following page: 
[BlueCompute](https://github.com/ibm-cloud-architecture/refarch-cloudnative-kubernetes)

## Register the BlueCompute repository

The first step is to the register the BlueCompute repository in IBM Cloud private. Follow these steps after logging in to IBM Cloud private UI:

* Click the Menu option
* Select *System*
* Click the *Repositories* tab
* Click *Add Repository*
* Type:
** Repository Name: BlueCompute
** URL: https://raw.githubusercontent.com/ibm-cloud-architecture/refarch-privatecloud/master/charts/stable

## Deploy the BlueCompute application

Now let's deploy the BlueCompute application, by following these steps:

* Click the Menu option
* Click *AppCenter*
* In the Search toolbox, type Blue. You should see the following application:

![alt text](Deploing/BlueCompute.png "Menu") 

* Click *Install Package*
