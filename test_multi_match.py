import fitz, re
path='上海人工智能训练师三级理论题库和答案2025.pdf'
doc=fitz.open(path)
text=''.join([doc.load_page(i).get_text('text')+'\n' for i in range(doc.page_count)])
# show occurrences of the 20 characters before and after
for m in re.finditer('多选题', text):
    i = m.start()
    print('\n--- occurrence at', i, '---')
    print(text[max(0,i-20):i+40])

pattern = r'三[、,，]\s*多选题([\s\S]*?)(?:四[、,，]\s*|答案|参考答案|$)'
mm = re.search(pattern, text)
print('\npattern match?', bool(mm))
if mm:
    s = mm.group(1)
    print('matched length', len(s))
    print('preview:\n', s[:800])
else:
    print('no match; trying relaxed pattern')
    mm2 = re.search(r'多选题([\s\S]*?)(?:四[、,，]|答案|参考答案|$)', text)
    print('relaxed match?', bool(mm2))
    if mm2:
        print('len', len(mm2.group(1)))
        print(mm2.group(1)[:800])
# debug: show the full matched region and nearby '四' occurrences
for m in re.finditer(r'三[、,，]\s*多选题', text):
    i = m.start()
    print('\n--- DEBUG around multi at', i, '---')
    print('next 200 chars:')
    print(text[i:i+200])
    next_four = text.find('四', i)
    print('next 四 at', next_four)
    if next_four != -1:
        print('slice to next 四 (len):', len(text[i:next_four]))
        print(text[i:next_four])
