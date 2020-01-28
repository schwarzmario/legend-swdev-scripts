import sys, os, subprocess, re

usage = '''
Usage: 

python /path/to/installMaGe.py (/optional/installation/path or clean)

This script can be run from anywhere. It downloads and compiles MGDO, MaGe, and
GAT in the directory from which it is executed. It also runs make install on
MGDO and MaGe, installing them to /root/.local, or an alternative installation
location of your choice.

Instructions:
cd /path/to/directory/where/you/want/the/source/code/to/be
mkdir /installation/path/if/it/doesn't/exist
python /path/to/installMaGe.py (/optional/installation/path)
source setup_mage.sh
python /path/to/installMaGe.py (/optional/installation/path)
[follow instructions]

You will be prompted to enter your github credentials to download each package
before they are compiled.

To remove the installation, from the same directory containing the source code, do:

python /path/to/installMaGe.py clean
'''

help_strings = ['h', '-h', '--h', 'help', '-help', '--help']
# check for the right number of arguments
if len(sys.argv) > 2 or (len(sys.argv) > 1 and sys.argv[1] in help_strings):
    print(usage)
    sys.exit()

# clean up if desired
if len(sys.argv) == 2 and sys.argv[1] == 'clean':
    if os.path.exists('MaGe/GNUmakefile'):
      os.chdir('MaGe')
      subprocess.run(['make', 'uninstall'])
      os.chdir('..')
    if os.path.exists('MGDO/Makefile'):
        os.chdir('MGDO')
        subprocess.run(['make', 'uninstall'])
        os.chdir('..')
    subprocess.run(['rm', '-rf', 'MGDO', 'MaGe', 'GAT', 'setup_mage.sh'])
    sys.exit()

# determine install_path 
install_path = '/root/.local'
if len(sys.argv) == 2: install_path = sys.argv[1]
if not os.path.isdir(install_path):
    print(install_path, 'is not an existing directory')
    print(usage)
    sys.exit()

# store pwd
pwd = subprocess.run(['pwd'], capture_output=True, encoding="utf-8").stdout.rstrip()

# determine geant4, generate setup_mage.sh, and source it
if not 'G4INSTALL' in os.environ:
    print('Generating setup_mage.sh ...')
    g4path = re.sub('data/G4EMLOW.*', '', os.environ['G4LEDATA'])
    gatlibs = '$GATDIR/BaseClasses:$GATDIR/MGTEventProcessing' \
            + ':$GATDIR/MGOutputMCRunProcessing:$GATDIR/Analysis' \
            + ':$GATDIR/MJDAnalysis:$GATDIR/DCProcs'
    with open('setup_mage.sh', 'w') as file:
        file.write('source ' + g4path + 'geant4make/geant4make.sh\n')
        file.write('export MGDODIR=' + pwd + '/MGDO\n')
        file.write('export TAMDIR=$MGDODIR/tam\n')
        file.write('export MAGEDIR=' + pwd + '/MaGe\n')
        file.write('export MGGENERATORDATA=' + pwd + '/MaGe/generators/data\n')
        file.write('export GATDIR=' + pwd + '/GAT\n')
        file.write('export PATH=' + install_path + '/bin:$GATDIR/Apps:$PATH\n')
        file.write('export LD_LIBRARY_PATH=' + install_path + '/lib:' + gatlibs + ':$TAMDIR/lib:$LD_LIBRARY_PATH\n')
        file.write('export ROOT_INCLUDE_PATH=${CLHEP_INCLUDE_DIR}:' \
                   + install_path + '/include:$TAMDIR:$GATDIR/BaseClasses:' \
                   + '$GATDIR/MGTEventProcessing:$GATDIR/MGOutputMCRunProcessing:$GATDIR/PFunc\n')

    print('Please do:')
    print('source setup_mage.sh')
    print('python', ' '.join(sys.argv))
    sys.exit()


# download (user will enter password)
try:
    if not os.path.exists('MGDO'):
        subprocess.run(['git', 'clone', 'https://github.com/mppmu/MGDO.git'], check=True)
    if not os.path.exists('MaGe'):
        subprocess.run(['git', 'clone', 'https://github.com/mppmu/MaGe.git'], check=True)
    if not os.path.exists('GAT'):
        subprocess.run(['git', 'clone', 'https://github.com/mppmu/GAT.git'], check=True)
except subprocess.CalledProcessError:
    sys.exit()

# install MGDO
os.chdir('MGDO')
subprocess.run(['./configure', '--prefix='+install_path, '--enable-majorana-all'])
subprocess.run(['make'])
subprocess.run(['make', 'install'])
os.chdir('..')

# install MaGe
os.chdir('MaGe')
subprocess.run(['./configure', '--prefix='+install_path, '--disable-g4gdml'])
subprocess.run(['make'])
subprocess.run(['make', 'install'])
os.chdir('..')

# install GAT
os.chdir('GAT')
subprocess.run(['make'])
os.chdir('..')

print('Installation complete. If desired, add the following line to your login script.')
print('source', pwd + '/setup_mage.sh')

