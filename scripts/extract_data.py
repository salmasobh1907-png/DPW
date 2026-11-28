"""Copy the data block out of the page into a JSON file.
Usage: python3 extract_data.py ../app/DP_World_Platform_DEMO.html demo_data.json
The page keeps all its starting data on ONE line that begins with `const DATA = `."""
import sys, re, json
s = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'^const DATA = (.*);\s*$', s, re.M)
json.dump(json.loads(m.group(1)), open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('written', sys.argv[2])
