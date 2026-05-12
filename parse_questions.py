import fitz
import re
from pathlib import Path

path = Path('上海人工智能训练师三级理论题库和答案2025.pdf')
doc = fitz.open(path)
text = ''.join([doc.load_page(i).get_text('text') + '\n' for i in range(doc.page_count)])

# locate sections (support multiple separator characters such as '、', ',' and '，')
judgment_match = re.search(r'一[、,，]\s*判断题([\s\S]*?)二[、,，]\s*单选题', text)
single_match = re.search(r'二[、,，]\s*单选题', text)

if not judgment_match or not single_match:
    raise SystemExit('Failed to locate judgment or single sections')

judgment_text = judgment_match.group(1)
# single_text = content between 二、单选题 and 三、多选题 (if exists)
single_start = single_match.start()
single_heading_end = single_match.end()
three_heading = re.search(r'三[、,，]\s*多选题', text)
if three_heading:
    single_text = text[single_heading_end:three_heading.start()]
else:
    single_text = text[single_heading_end:]

# Extract multi section robustly: find the '三、多选题' heading then slice until the next '四、' heading (line-start)
multi_text = ''
three_heading = re.search(r'三[、,，]\s*多选题', text)
if three_heading:
    start_idx = three_heading.end()
    end_search = re.search(r'\n\s*四[、,，]\s*', text[start_idx:])
    if end_search:
        end_idx = start_idx + end_search.start()
    else:
        end_idx = len(text)
    multi_text = text[start_idx:end_idx]

# Parse judgment questions (unchanged)
judgments = []
current = None
for line in judgment_text.splitlines():
    line = line.strip()
    if not line:
        continue
    m = re.match(r'^[（(]([✓✕])[)）]\s*(\d+)\.\s*(.*)$', line)
    if m:
        if current:
            judgments.append(current)
        current = {
            'id': int(m.group(2)),
            'type': 'judgment',
            'text': m.group(3).strip(),
            'answer': True if m.group(1) == '✓' else False
        }
    elif current:
        current['text'] += ' ' + line
if current:
    judgments.append(current)

def _extract_paren_answer(text):
    """If text contains a parenthesized letter or letters (ASCII or fullwidth),
    return (clean_text, letters) where clean_text preserves the parentheses
    but removes the letters inside. letters is a list of letters found.
    """
    m = re.search(r'[（(]\s*([A-Za-z][A-Za-z,，\s]*)\s*[)）]', text)
    if not m:
        return text, None
    raw = m.group(1)
    letters = re.findall(r'[A-Za-z]', raw)
    clean = re.sub(r'([（(])\s*[A-Za-z][A-Za-z,，\s]*\s*([)）])', r'\1\2', text)
    return clean.strip(), letters


# Parse single-choice questions (kept compatible)
singles = []
current = None
for line in single_text.splitlines():
    stripped = line.strip()
    if not stripped:
        continue
    qnum_only = re.match(r'^(\d+)\s*$', stripped)
    qnum_and_text = re.match(r'^(\d+)\s+(.*)$', stripped)
    if qnum_only:
        if current:
            singles.append(current)
        current = {'id': int(qnum_only.group(1)), 'type': 'single', 'text': '', 'options': {}, 'answer': None}
        continue
    if qnum_and_text and current and not current['text'] and not current['options']:
        current = {'id': int(qnum_and_text.group(1)), 'type': 'single', 'text': qnum_and_text.group(2).strip(), 'options': {}, 'answer': None}
        clean, letters = _extract_paren_answer(current['text'])
        if letters:
            current['answer'] = letters[0].upper()
            current['text'] = clean
        continue
    # Only treat a line as an option if the letter is followed by a separator
    # such as a dot, Chinese enumeration mark、, fullwidth dot, closing parenthesis or whitespace.
    # This prevents question lines that start with an English word (e.g. "Figma ...")
    # from being misinterpreted as an option.
    if current and re.match(r'^\(?[A-Za-z]\)?[\.、．\)\s]+', stripped):
        opt_match = re.match(r'^\(?([A-Za-z])\)?[\.、．\)\s]+(.*)$', stripped)
        if opt_match:
            key = opt_match.group(1).upper()
            rest = opt_match.group(2).strip()
            if key in current['options']:
                current['options'][key] += ' ' + rest
            else:
                current['options'][key] = rest
            continue
    if current:
        if current['options']:
            last = list(current['options'])[-1]
            current['options'][last] += ' ' + stripped
        else:
            current['text'] += (' ' + stripped if current['text'] else stripped)

if current:
    singles.append(current)

for q in singles:
    clean, letters = _extract_paren_answer(q['text'])
    if letters:
        q['answer'] = letters[0].upper()
        q['text'] = clean
    # preserve insertion order of options
    q['options'] = [{'key': k, 'text': v} for k, v in q['options'].items()]

# Parse multiple-choice questions
multis = []
current = None
for line in multi_text.splitlines():
    stripped = line.strip()
    if not stripped:
        continue
    qnum_only = re.match(r'^(\d+)\s*$', stripped)
    qnum_and_text = re.match(r'^(\d+)\s+(.*)$', stripped)
    if qnum_only:
        if current:
            multis.append(current)
        current = {'id': int(qnum_only.group(1)), 'type': 'multiple', 'text': '', 'options': {}, 'answer': None}
        continue
    if qnum_and_text and current and not current['text'] and not current['options']:
        current = {'id': int(qnum_and_text.group(1)), 'type': 'multiple', 'text': qnum_and_text.group(2).strip(), 'options': {}, 'answer': None}
        # inline answer like (AC) or (A,B)
        ans_inline = re.search(r'\(\s*([A-Za-z][A-Za-z,，\s]*)\s*\)', current['text'])
        if ans_inline:
            raw = ans_inline.group(1)
            letters = re.findall(r'[A-Za-z]', raw)
            current['answer'] = sorted(list({l.upper() for l in letters}))
            current['text'] = re.sub(r'\(\s*[A-Za-z][A-Za-z,，\s]*\s*\)', '', current['text']).strip()
        continue
    # Same stricter rule for multiple-choice parsing
    if current and re.match(r'^\(?[A-Za-z]\)?[\.、．\)\s]+', stripped):
        opt_match = re.match(r'^\(?([A-Za-z])\)?[\.、．\)\s]+(.*)$', stripped)
        if opt_match:
            key = opt_match.group(1).upper()
            rest = opt_match.group(2).strip()
            if key in current['options']:
                current['options'][key] += ' ' + rest
            else:
                current['options'][key] = rest
            continue
    if current:
        if current['options']:
            last = list(current['options'])[-1]
            current['options'][last] += ' ' + stripped
        else:
            current['text'] += (' ' + stripped if current['text'] else stripped)

if current:
    multis.append(current)

# finalize multiple answers and normalize
for q in multis:
    if q['answer'] is None:
        ans = re.search(r'答案[:：]\s*([A-Za-z,，\s]+)', q['text'])
        if ans:
            raw = ans.group(1)
            letters = re.findall(r'[A-Za-z]', raw)
            q['answer'] = sorted(list({l.upper() for l in letters}))
            q['text'] = re.sub(r'答案[:：]\s*[A-Za-z,，\s]+', '', q['text']).strip()
        else:
            ans2 = re.search(r'\(\s*([A-Za-z][A-Za-z,，\s]*)\s*\)', q['text'])
            if ans2:
                letters = re.findall(r'[A-Za-z]', ans2.group(1))
                q['answer'] = sorted(list({l.upper() for l in letters}))
                q['text'] = re.sub(r'\(\s*[A-Za-z][A-Za-z,，\s]*\s*\)', '', q['text']).strip()
    q['options'] = [{'key': k, 'text': v} for k, v in sorted(q['options'].items())]
    if q['answer'] is None:
        q['answer'] = []
    else:
        q['answer'] = sorted(list({a.upper() for a in q['answer']}))

out = {'judgment': judgments, 'single': singles, 'multiple': multis}

with open('parsed_questions.json', 'w', encoding='utf-8') as f:
    import json
    json.dump(out, f, ensure_ascii=False, indent=2)
print('parsed', len(judgments), 'judgment questions,', len(singles), 'single-choice questions and', len(multis), 'multiple-choice questions')
