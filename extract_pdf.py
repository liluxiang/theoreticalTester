import fitz
path = '上海人工智能训练师三级理论题库和答案2025.pdf'
with fitz.open(path) as doc:
    print('pages', doc.page_count)
    for i in range(min(5, doc.page_count)):
        text = doc.load_page(i).get_text('text')
        print('--- PAGE', i + 1, '---')
        print(text[:1200])
        print('--- END PAGE', i + 1, '---\n')
