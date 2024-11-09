import subprocess

script = "v3_exercise_tcp_group_chat.py"
args1 = ["user1", "3000", "127.0.0.1:3001", "127.0.0.1:3002"]
args2 = ["user2", "3001", "127.0.0.1:3000", "127.0.0.1:3002"]
args3 = ["user3", "3002", "127.0.0.1:3000", "127.0.0.1:3001"]

# Ci sono errori di EOF e di socket chiuse e non rimosse dalla lista

commands = [
    f"python {script} {' '.join(args1)}",
    f"python {script} {' '.join(args2)}",
    f"python {script} {' '.join(args3)}"
]

# processes = [
#     subprocess.Popen(['xfce4-terminal', '--hold', '-e', f"bash -c '{cmd}'"]) for cmd in commands
# ]

processes = [
    subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for cmd in commands
]

try:
    for i, process in enumerate(processes):
        # Example of writing to stdin
        process.stdin.write("Hello! \n")
        process.stdin.flush()
        
        # Reading output
        stdout, stderr = process.communicate()
        print(f"Process {i+1} Output:\n {stdout}\n\n")
        print(f"Process {i+1} Error: \n{stderr}\n\n")
except Exception as e:
    print(e)