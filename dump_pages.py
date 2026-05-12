import fitz
path='上海人工智能训练师三级理论题库和答案2025.pdf'
with fitz.open(path) as doc:
    for i in range(90, 96):
        text = doc.load_page(i).get_text('text')
        print('--- PAGE', i+1, '---')
        print(text[:1600])
        print('--- END PAGE', i+1, '---\n')
