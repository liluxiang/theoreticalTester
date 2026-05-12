import fitz
path='上海人工智能训练师三级理论题库和答案2025.pdf'
doc=fitz.open(path)
keywords = ['多选题','单选题','判断题','填空题','名词解释','简答题','综合题']
for i in range(doc.page_count):
    text = doc.load_page(i).get_text('text')
    matches = [line for line in text.splitlines() if any(k in line for k in keywords)]
    if matches:
        print('PAGE', i+1)
        for line in matches:
            print(' ', line)
