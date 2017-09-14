import os
import json

with open('package.json', 'r') as f:
    data = json.load(f)
    for package in data["dependencies"].keys():
		os.system("npm install %s --save"%(package,))
