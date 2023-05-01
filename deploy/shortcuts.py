import os
import subprocess

from logger.models import Log


def write_superuser(text, path):
    command = ['sudo', 'tee', path]
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        proc.stdin.write(text.encode('utf-8'))
        proc.stdin.close()
        proc.wait()

        if proc.returncode != 0:
            Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='write_superuser',
                               message=f'Could not write to {path} with error: {proc.stderr.read().decode("utf-8")}')
    return True


def execute_command(command: str) -> bool:
    Log.objects.create(log_type=Log.LOG_TYPE_COMMAND, location='execute_command',
                       message=command)
    result = os.popen(command).read()
    if result != '':
        Log.objects.create(log_type=Log.LOG_TYPE_ERROR, location='execute_command',
                           message=f'Command "{command}" failed with result: {result}')
    return True
