import json
import subprocess

with open('config.json') as f:
    config = json.load(f)


def check_docker():
    progress = subprocess.run(['docker', 'info'], capture_output=True, text=True)
    if len(progress.stderr) > 0 and 'error' in progress.stderr.lower():
        raise RuntimeError('Docker is not launched or running normally!')


#check_docker()
