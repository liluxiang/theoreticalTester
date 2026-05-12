import json
from pathlib import Path
p = Path('parsed_questions.json')
q = Path('questions.js')
with p.open('r', encoding='utf-8') as f:
    data = json.load(f)
with q.open('w', encoding='utf-8') as f:
    f.write('const QUIZ_DATA = ')
    json.dump(data, f, ensure_ascii=False)
    f.write(';\n')
print('written', q)
