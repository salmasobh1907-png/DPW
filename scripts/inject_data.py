"""Put a JSON data file back into the page (replaces only the `const DATA = ...;` line).
Usage: python3 inject_data.py ../app/DP_World_Platform_DEMO.html demo_data.json [out.html]"""
import sys, json
page, data = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else page
lines = open(page, encoding='utf-8').read().split('\n')
i = next(i for i, l in enumerate(lines) if l.strip().startswith('const DATA = '))
D = json.load(open(data, encoding='utf-8'))
lines[i] = 'const DATA = ' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';'
open(out, 'w', encoding='utf-8').write('\n'.join(lines))
print('data line replaced in', out)
