import sys, os, subprocess, re, argparse

usage = '''
Usage: 

python /path/to/installMaGe.py (/optional/installation/path or clean)

This script can be run from anywhere. It downloads and compiles MGDO, MaGe, and
mage-post-proc in the directory from which it is executed. It also runs make
install, installing to the current directory, or an alternative installation
location of your choice.

You will be prompted to enter your github credentials to download each package
before they are compiled.

To remove the installation, from the same directory containing the source code, do:

python /path/to/installMaGe.py clean
'''

parser = argparse.ArgumentParser(description = usage)

parser.add_argument('command', type=str,
                    choices=['install', 'clean', 'reinstall'],
                    help="What action to take. Options:\n"\
                    "  install: install from scratch\n"\
                    "  clean: uninstall and remove\n"\
                    "  reinstall: clean and then install\n")
parser.add_argument('-b', '--buildpath', type=str, default='.',
                    help="Base path to build software in")
parser.add_argument('-i', '--installpath', type=str,
                    help="Base path to install software in. By default use the build path.")
parser.add_argument('-j', '--jobs', type=int, default=1,
                    help="Number of threads to run with Make")

parser.add_argument('--mgdofork', type=str, default='mppmu',
                    help="Github fork to install MGDO from")
parser.add_argument('--mgdobranch', type=str, default='master',
                    help="Git branch to install MGDO from")
parser.add_argument('--magefork', type=str, default='mppmu',
                    help="Github fork to install MaGe from")
parser.add_argument('--magebranch', type=str, default='master',
                    help="Git branch to install MaGe from")
parser.add_argument('--mppfork', type=str, default='legend-exp',
                    help="Github fork to install MPP from")
parser.add_argument('--mppbranch', type=str, default='master',
                    help="Git branch to install MPP from")
args = parser.parse_args()

original_pwd = os.getcwd()
os.makedirs(args.buildpath, exist_ok=True)
os.chdir(args.buildpath)
pwd = os.getcwd()

# determine install_path 
install_path = args.installpath if args.installpath else pwd
if not os.path.isdir(install_path):
    print(install_path, 'is not an existing directory')
    print(usage)
    sys.exit()

# make absolutely sure necessary variables are set for (un)installation
os.environ['MGDODIR']=pwd+'/MGDO'
os.environ['PATH']=install_path+'/bin:'+os.environ['PATH']

# clean up if desired
if args.command == 'clean' or args.command == 'reinstall':
    if os.path.exists('mage-post-proc/Makefile'):
        os.chdir('mage-post-proc')
        subprocess.run(['make', 'uninstall', '-j1'])
        os.chdir('..')
    if os.path.exists('MaGe/build/install_manifest.txt'):
        subprocess.run('xargs -L1 rm -vf'.split(), stdin=open('MaGe/build/install_manifest.txt'))
        subprocess.run('rm -vf Mage/build/install_manifest.txt'.split())
    if os.path.exists('MGDO/Makefile'):
        os.chdir('MGDO')
        subprocess.run(['make', 'uninstall', '-j1'])
        os.chdir('..')
    subprocess.run(['rm', '-rf', 'MGDO', 'MaGe', 'mage-post-proc', 'setup_mage.sh'])
    if args.command == 'clean':
        sys.exit()

# find CLHEP
try:
    clhep_include_dir = os.environ.get('CLHEP_BASE_DIR', None)
    if clhep_include_dir is None:
        clhep_include_dir = subprocess.run(['clhep-config','--prefix'], check=True, universal_newlines=True, stdout=subprocess.PIPE).stdout.split('"')[1]
    clhep_include_dir = clhep_include_dir + '/include'
except Exception:
    print("Could not find CLHEP_BASE_PATH or clhep-config")
    sys.exit()

# determine geant4, generate setup_mage.sh, and source it
print('Generating setup_mage.sh ...')
g4path = re.sub('data/G4EMLOW.*', '', os.environ['G4LEDATA'])
with open('setup_mage.sh', 'w') as file:
    file.write(f'source {g4path}geant4make/geant4make.sh\n')
    file.write(f'export MGDODIR={pwd}/MGDO\n')
    file.write(f'export TAMDIR=$MGDODIR/tam\n')
    file.write(f'export MAGEDIR={pwd}/MaGe/build\n')
    file.write(f'export MGGENERATORDATA={pwd}/share/MaGe/generators\n')
    file.write(f'export MGGERDAGEOMETRY={pwd}/share/MaGe/gerdageometry\n')
    file.write(f'export MPPDIR={pwd}/mage-post-proc\n')
    file.write(f'export PATH={install_path}/bin:$PATH\n')
    file.write(f'export LD_LIBRARY_PATH={install_path}/lib:$LD_LIBRARY_PATH\n')
    file.write(f'export ROOT_INCLUDE_PATH={clhep_include_dir}:' \
               f'{install_path}/include/mgdo:' \
               f'{install_path}/include/tam:$TAMDIR:' \
               f'{install_path}/include/mage:' \
               f'{install_path}/include/mage-post-proc:' \
               '${ROOT_INCLUDE_PATH}\n')
    file.write(f'export PYTHONPATH={install_path}/lib:$PYTHONPATH\n')

# download (user will enter password)
try:
    if not os.path.exists('MGDO'):
        subprocess.run(f'git clone -b {args.mgdobranch} https://github.com/{args.mgdofork}/MGDO.git'.split(), check=True)
    if not os.path.exists('MaGe'):
        subprocess.run(f'git clone -b {args.magebranch} https://github.com/{args.magefork}/MaGe.git MaGe/source'.split(), check=True)
    if not os.path.exists('mage-post-proc'):
        subprocess.run(f'git clone -b {args.mppbranch} https://github.com/{args.mppfork}/mage-post-proc.git'.split(), check=True)
except subprocess.CalledProcessError:
    sys.exit()
    
# install MGDO
os.chdir('MGDO')
subprocess.run(f'./configure --prefix={install_path} --enable-streamers --enable-tam --enable-tabree'.split())
subprocess.run(['make', f'-j{args.jobs}'])
if args.jobs>1:
    subprocess.run(['make', '-j1']) # make -j>1 doesn't always succeed
subprocess.run(['make', 'install', '-j1'])
os.chdir('..')

# install MaGe
subprocess.run(f'cmake -S MaGe/source -B MaGe/build -DCMAKE_INSTALL_PREFIX={install_path}'.split())
os.chdir('MaGe/build')
subprocess.run(['make', f'-j{args.jobs}'])
subprocess.run(['make', 'install', '-j1'])
os.chdir('../..')

# install mage-post-proc
os.chdir('mage-post-proc')
subprocess.run(['make', f'-j{args.jobs}'])
if args.jobs>1:
    subprocess.run(['make', '-j1']) # make -j>1 doesn't always succeed
subprocess.run(['make', 'install', '-j1'])
os.chdir(original_pwd)

print('Installation complete. If desired, add the following line to your login script.')
print('source', pwd + '/setup_mage.sh')

