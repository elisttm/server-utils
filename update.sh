#!/bin/bash

set -e
set -x

sudo apt autoremove -y
sudo apt autoclean -y
sudo apt clean -y

sudo apt update -y
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt autoclean -y
sudo apt clean -y