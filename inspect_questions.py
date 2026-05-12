import fitz, re
from pathlib import Path
path = Path('上海人工智能训练师三级理论题库和答案2025.pdf')
doc = fitz.open(path)
text = ''.join([doc.load_page(i).get_text('text') + '\n' for i in range(doc.page_count)])
for qid in [130, 218, 275, 276, 277, 278, 279]:
    print('===', qid, '===')
    start = re.search(rf'(^|\n)\s*{qid}\b', text)
    if not start:
        print('NOT FOUND START')
        continue
    start_pos = start.start()
    end = re.search(rf'\n\s*{qid+1}\b', text[start_pos:])
    if end:
        block = text[start_pos:start_pos+end.start()]
    else:
        block = text[start_pos:start_pos+4000]
    print(block)
    print()
