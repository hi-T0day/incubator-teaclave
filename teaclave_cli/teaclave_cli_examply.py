#!/usr/bin/python
""" This Python Script is an example to use CLI, which can instead of py_file example  """
import json
import subprocess
import base64
CONFIG = {
    "tdfs":{
        "name":"tdfs",
        "ipport":"127.0.0.1:5065"
    },
    "tms":{
        "name":"tms",
        "ipport":"127.0.0.1:5554"
    },
    "fns":{
        "name":"fns",
        "ipport":"127.0.0.1:3444"
    },
    "enclave_info": "enclave_info.toml",
    "user_id":"uid",
    "user_token":"token",
    "function_name": "mesapy_from_buffer",
    "upload_file_name":"1.txt",
    "upload_file_path":"./1.txt",
    "invoke_payload_file_path": "./payload.py",
    "collaborator_list": []
}
def upload():
    meta_result = json.loads(subprocess.check_output( \
        ['./teaclave_cli', 'file', CONFIG['upload_file_path'], '--method', 'meta']))
    file_sha256, file_size = meta_result["sha256"], meta_result["size"]
    upload_payload = {"type": "Create", "user_id": CONFIG["user_id"], \
            "user_token": CONFIG["user_token"], "file_name": CONFIG["upload_file_name"], \
            "sha256": file_sha256, "file_size": file_size}
    upload_cmd = subprocess.Popen(['./teaclave_cli', 'connect', CONFIG['tdfs']['ipport'], \
        '--enclave_info', CONFIG['enclave_info'], '--endpoint', CONFIG['tdfs']['name']], \
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    upload_result = json.loads(upload_cmd.communicate(input=json.dumps(upload_payload))[0])
    subprocess.check_output(['./teaclave_cli', 'file', CONFIG['upload_file_path'], \
            '--method', 'encrypt', '--key_config', json.dumps(upload_result)])
    return upload_result["file_id"], upload_result["key_config"]

def task(file_id):
    task_payload = {"type":"Create", "function_name":CONFIG["function_name"], \
            "collaborator_list":CONFIG["collaborator_list"], "files":[file_id], \
            "user_id": CONFIG["user_id"], "user_token":CONFIG["user_token"]}
    task_cmd = subprocess.Popen(['./teaclave_cli', 'connect', '127.0.0.1:5554', \
            '--enclave_info', 'enclave_info.toml', '--endpoint', 'tms'], \
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    task_result = json.loads(task_cmd.communicate(input=json.dumps(task_payload))[0])
    return task_result['task_id'], task_result['task_token']

def invoke(task_id, task_token):
    with open(CONFIG["invoke_payload_file_path"], 'rb') as payload_file_obj:
        payload_file = payload_file_obj.read()
        payload_file_base64 = base64.b64encode(payload_file)
    invoke_payload = {"task_id": task_id, "task_token": task_token, \
            "function_name":CONFIG["function_name"], "payload": payload_file_base64}
    invoke_cmd = subprocess.Popen(['./teaclave_cli', 'connect', CONFIG['fns']['ipport'], \
            '--enclave_info', CONFIG['enclave_info'], '--endpoint', CONFIG['fns']['name']], \
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    invoke_result = json.loads(invoke_cmd.communicate(input=json.dumps(invoke_payload))[0])
    return invoke_result["result"]


if __name__ == "__main__":
    FILE_ID, KEY_CONFIG = upload()
    TASK_ID, TASK_TOKEN = task(FILE_ID)
    RESULT = invoke(TASK_ID, TASK_TOKEN)
    CONFIG["file_id"] = FILE_ID
    CONFIG["key_config"] = KEY_CONFIG
    CONFIG["result"] = RESULT
    with open('./output.json', 'w') as f:
        f.write(json.dumps(CONFIG, indent=4))
