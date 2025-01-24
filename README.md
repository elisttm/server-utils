# my custom server utilities

this is a collection of random scripts and configs i use to help me manage my dedicated server

these are not intended to be taken and used by others as these are made explicitly for my own workflow, i just have them here to reference,

## start-template.sh
this is the template i use for starting python scripts or cli server apps. the -qDRS args do as follows:
- **q**: supresses errors just to reduce annoyances
- **DR**: if the specified screen exists, detach any existing sessions and reattach here immediately. if it doesnt exist, create it
- **S**: specifies the name of/for the screen, "NAME" in this example

## autorun.sh
a script that runs on startup whenever my server reboots that autoruns aformentioned screen-based start scripts. it importantly replaces the args with ones that defer the scripts to the background

## restarter.py

a python script i have set to run at 6am EST every day. it is a grossly overengineered autonomous restart script that checks, restarts and updates servers in accordance to my workflow. it supports restarting multiple servers of the same group if they share a directory as well.