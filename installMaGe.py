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
parser.add_argument('-a', '--authentication', type=str,
                    choices=['ssh', 'https'], default='ssh',
                    help="""github authentication method. Options:
                        ssh: ssh-rsa key
                        https: personal access token""")
parser.add_argument('-j', '--jobs', type=int, default=1,
                    help="Number of threads to run with Make")

parser.add_argument('--mgdofork', type=str, default='mppmu',
                    help="Github fork to install MGDO from")
parser.add_argument('--mgdobranch', type=str, default='master',
                    help="Git branch to install MGDO from")
parser.add_argument('--magefork', type=str, default='mppmu',
                    help="Github fork to install MaGe from")
parser.add_argument('--magebranch', type=str, default='main',
                    help="Git branch to install MaGe from")
parser.add_argument('--mppfork', type=str, default='legend-exp',
                    help="Github fork to install MPP from")
parser.add_argument('--mppbranch', type=str, default='main',
                    help="Git branch to install MPP from")

parser.add_argument('--pipinstallglobal',  action='store_true', default=False,
                    help="Install magepostproc module to global site-packages")
parser.add_argument('--pipinstalluser',  action='store_true', default=False,
                    help="Install magepostproc module to user site-packages")

args = parser.parse_args()

original_pwd = os.getcwd()
os.makedirs(args.buildpath, exist_ok=True)
os.chdir(args.buildpath)
pwd = os.getcwd()

# helper function to run command line commands. Print command, then run it, and raise errors on failure
def cmd(command):
    print(command)
    subprocess.run(command, shell=True, check=True)

# Disable conda for configure/cmake steps if needed
preconfigure = ''
if os.path.exists(os.path.join(sys.prefix, 'conda-meta')):
    print("Disabling conda for configure steps...")
    preconfigure = 'source disable-conda.sh; '

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
    if os.path.exists('mage-post-proc/build/install_manifest.txt'):
        subprocess.run('xargs -L1 rm -vf'.split(), stdin=open('mage-post-proc/build/install_manifest.txt'))
        subprocess.run('rm -vf mage-post-proc/build/install_manifest.txt'.split())
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
    file.write(f'export PYTHONPATH={install_path}/lib/magepostproc:$PYTHONPATH\n')

# download (user will enter password)
try:
    address = 'git@github.com:' if args.authentication=='ssh' else\
              'https://github.com/'
    if not os.path.exists('MGDO'):
        cmd(f'git clone -b {args.mgdobranch} {address}{args.mgdofork}/MGDO.git')
    if not os.path.exists('MaGe'):
        cmd(f'git clone -b {args.magebranch} {address}{args.magefork}/MaGe.git MaGe/source')
    if not os.path.exists('mage-post-proc'):
        cmd(f'git clone -b {args.mppbranch} {address}{args.mppfork}/mage-post-proc.git mage-post-proc/mage-post-proc')
except subprocess.CalledProcessError:
    sys.exit()

# install MGDO
os.chdir('MGDO')
cmd(f'{preconfigure}./configure --prefix={install_path} --enable-streamers --enable-tam --enable-tabree')
cmd(f'make svninfo static -j{args.jobs}')
cmd('make')
cmd('make install')
os.chdir('..')

# install MaGe
root_cflags = subprocess.check_output("root-config --cflags".split()).decode("utf-8")
cppstd = re.search("-std=c\+\+(\d*)", root_cflags)
cppstd = f"-DCMAKE_CXX_STANDARD={cppstd.group(1)}" if cppstd else ""
cmd(f'{preconfigure}cmake -S MaGe/source -B MaGe/build {cppstd} -DCMAKE_INSTALL_PREFIX={install_path}')
os.chdir('MaGe/build')
cmd(f'make -j{args.jobs}')
cmd('make install')
os.chdir('../..')

# install mage-post-proc
mpp_cmake_opts = ''
if(args.pipinstallglobal):
    mpp_cmake_opts += f" -DPYTHON_EXE={sys.executable} -DPIP_GLOBAL_INSTALL=ON"
if(args.pipinstalluser):
    mpp_cmake_opts += f" -DPYTHON_EXE={sys.executable} -DPIP_USER_INSTALL=ON"

os.chdir('mage-post-proc')
cmd(f'{preconfigure}cmake -S mage-post-proc -B build -DCMAKE_INSTALL_PREFIX={install_path} {mpp_cmake_opts}')
cmd(f'make -Cbuild -j{args.jobs} install')
os.chdir(original_pwd)

print('Installation complete. If desired, add the following line to your login script.')
print('source', pwd + '/setup_mage.sh')

