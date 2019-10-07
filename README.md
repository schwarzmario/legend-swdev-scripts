# LEGEND Software Developer Scripts

This repository will hold scripts that will install softare for use with a legend container. 
See https://github.com/legend-exp/legendexp_legend-base_img for example.

## Getting Started

Pull these scipts and follow the directions.

## pygama_install.sh

Run from inside the legend container to install the full python suite in your directory outside of the container. You need to make sure an external volume is mounted inside the container.  

You need to edit the script after you download it to specify the path to the install directory. See notes inside the script.

## installMaGe.py

Installs MGDO, MaGe, and GAT for people with access to those repositories on mppmu. Typical usage:

```
mkdir [srcdir] [installdir]
cd [srcdir]
python /path/to/installMaGe.py [installdir]
source setup_mage.sh
python /path/to/installMaGe.py [installdir]
[enter github credentials 3 times if not automated]
[wait a while] 
[add source srcdir/setup_mage.sh to ~/.bashrc]
```

If something gets up, do `python /path/to/installMaGe.py clean` and try again
