import subprocess

result = subprocess.run(["arduino-cli board list"], shell=True, capture_output=True, text=True)

print(str(result.stdout))
