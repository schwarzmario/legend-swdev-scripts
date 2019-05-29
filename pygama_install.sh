#!/bin/bash
# pygama_install.sh                DJT   2019
#
# install pygama to local directory
# use this to install outside of conatiner (from inside of the container)
#    e.g. docker:legendexp/legend-base:latest
#
# Notes -
#  modify INSTALL_PREFIX to your personal directory
#  INSTALL_PREFIX dir needs to exist before running pygama_install.sh
#  you need to add PYTHONPATH to your login setup after installation (see below)
# -------------------------------------------------------------------------------
#
# set the install directory to where you want pygama to reside
export INSTALL_PREFIX=/global/homes/d/dave/legend2
#
# add this PYTHONPATH to you login setup
# needed for installation and running
#
if [ -z "$PYTHONPATH" ]; then
    export PYTHONPATH=${INSTALL_PREFIX}/pygama/lib/python3.7/site-packages
else
    export PYTHONPATH=$PYTHONPATH:${INSTALL_PREFIX}/pygama/lib/python3.7/site-packages
fi  
#
# get the latest pygama and set up directories
#
cd $INSTALL_PREFIX
git clone https://github.com/legend-exp/pygama.git
mkdir -p ${INSTALL_PREFIX}/pygama/lib/python3.7/site-packages
#
# do the installation
#
cd $INSTALL_PREFIX/pygama
python setup.py install --prefix=${INSTALL_PREFIX}/pygama
#
echo "done"
# -------------------------------------------------------------------------------
