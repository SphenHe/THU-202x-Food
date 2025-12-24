import PyInstaller.__main__
import platform
import os
import shutil

# Clean up previous build
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')

system = platform.system()
sep = ';' if system == 'Windows' else ':'

# Define data to include
# Format: 'source_path{sep}dest_path'
datas = [
    f'st.py{sep}.',
    f'utils{sep}utils',
    f'log.json{sep}.',
]

# PyInstaller arguments (minimize collected modules to reduce bundle size)
args = [
    'run_app.py',
    '--name=THU-Food-Summary',
    '--onefile',
    '--clean',
    '--collect-all=streamlit',
    '--collect-all=pandas',
    '--collect-all=matplotlib',
    '--collect-all=sklearn',
    '--hidden-import=streamlit',
    '--hidden-import=dotenv',
    '--hidden-import=Crypto.Cipher.AES',
    '--hidden-import=Crypto.Util.Padding',
    '--hidden-import=openai',
    '--hidden-import=requests',
    '--hidden-import=matplotlib.pyplot',
    '--hidden-import=sklearn.preprocessing'
]

# On Unix-like systems we can strip the binary to reduce size
if system != 'Windows':
    args.append('--strip')

# Add data arguments
for data in datas:
    args.append(f'--add-data={data}')

print(f"Building for {system} with args: {args}")

PyInstaller.__main__.run(args)
