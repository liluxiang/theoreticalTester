import fitz, re
path='上海人工智能训练师三级理论题库和答案2025.pdf'
doc=fitz.open(path)
text=''.join([doc.load_page(i).get_text('text')+'\n' for i in range(doc.page_count)])
out_lines = []
for m in re.finditer('多选题', text):
    start = max(0, m.start()-300)
    end = m.start()+400
    out_lines.append('\n--- MATCH at %d ---' % m.start())
    out_lines.append(text[start:end])

with open('multi_context.txt','w',encoding='utf-8') as f:
    f.write('\n'.join(out_lines))
print('wrote multi_context.txt')
