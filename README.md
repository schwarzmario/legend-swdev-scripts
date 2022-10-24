# LEGEND Software Developer Scripts

This repository will hold scripts that will install softare for use with a legend container.
See [legend-exp/legendexp_legend-base_img](https://github.com/legend-exp/legendexp_legend-base_img) for example.
Pull these scipts and follow the directions.

### `pygama_install.sh`

Run from inside the legend container to install the full python suite in your directory outside of the container. You need to make sure an external volume is mounted inside the container.  

You need to edit the script after you download it to specify the path to the install directory. See notes inside the script.

### `installMaGe.py`

Installs MGDO, MaGe, and GAT for people with access to those repositories on [mppmu](https://github.com/mppmu). Typical usage:

```console
$ mkdir [installdir]
$ python installMaGe.py --help # for help
$ python installMaGe.py install -i [installdir] -j8 # for example
$ echo "$PWD/setup_mage.sh" ~/.bashrc
```

If something gets up, do `python installMaGe.py clean` and try again.
