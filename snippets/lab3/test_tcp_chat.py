import subprocess
import threading
import time

# netstat -tlnp

script = "exercise_tcp_group_chat.py"
args1 = ["user1", "3000", "127.0.0.1:3001", "127.0.0.1:3002"]
args2 = ["user2", "3001", "127.0.0.1:3000", "127.0.0.1:3002"]
args3 = ["user3", "3002", "127.0.0.1:3000", "127.0.0.1:3001"]

# Ci sono errori di EOF, ma sono dovuti al metodo communicate()
# Threading normale forse funziona meglio, il thread usa subprocess, 
# oppure esegue direttamente quel codice

# Non capisco perché le cose terminino, forse perché il processo padre termina
# Meglio fare prima i test manuali

commands = [
    f"python {script} {' '.join(args1)}",
    f"python {script} {' '.join(args2)}",
    f"python {script} {' '.join(args3)}"
]

### Open a terminal for each process
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
        
        time.sleep(3)
        
        # kill the processes
        process.terminate() 
        stdout, stderr = process.communicate()
        print(f"Process {i+1} Output:\n {stdout}\n\n")
        print(f"Process {i+1} Error: \n{stderr}\n\n")
        
        # stdout = process.stdout.readline()
        # stderr = process.stderr.readline()
        # print(f"Process {i+1} Output:\n {stdout}\n\n")
        # print(f"Process {i+1} Error: \n{stderr}\n\n")

except Exception as e:
    print(e)
    

# wait for subprocess to end
for i, process in enumerate(processes):
    if process.poll() is None:
        print(f"Process {i+1} is still running")
    else:
        print(f"Process {i+1} has finished")