import re
import json
from pathlib import Path

p = Path('parsed_questions.json')
if not p.exists():
    raise SystemExit('parsed_questions.json not found')

data = json.loads(p.read_text(encoding='utf-8'))

paren_re = re.compile(r'[（(]\s*([A-Za-z][A-Za-z,，\s]*)\s*[)）]')
paren_remove_re = re.compile(r'([（(])\s*[A-Za-z][A-Za-z,，\s]*\s*([)）])')

allowed_single_keys = set(list('ABCD'))

def extract_paren_letters(text):
    m = paren_re.search(text)
    if not m:
        return None
    letters = re.findall(r'[A-Za-z]', m.group(1))
    return [l.upper() for l in letters]


def clean_paren_keep_brackets(text):
    return paren_remove_re.sub(r"\1\2", text).strip()


def process_question(q, allowed_keys=allowed_single_keys, is_multiple=False):
    # 1) extract parenthesized answer from question text
    letters = extract_paren_letters(q.get('text','') or '')
    if letters:
        if is_multiple:
            q['answer'] = sorted(list({l for l in letters}))
        else:
            if not q.get('answer'):
                q['answer'] = letters[0]
        q['text'] = clean_paren_keep_brackets(q.get('text','') or '')

    # 2) process options (list of {key,text}) preserving order
    opts = q.get('options') or []
    items = [(o.get('key',''), o.get('text','')) for o in opts]

    # 3) detect misclassified question text inside options
    if not q.get('text') or len((q.get('text') or '').strip()) < 8:
        for i, (k, v) in enumerate(items):
            if not v:
                continue
            # 增强的误分类检测：包含常见题干提示词、过长文本、以序号开头、以破折号开头，或包含空括号/方法/score 关键词
            suspect = False
            if re.search(r'(步骤|其中|使用方法|ETL|第[一1]个|步骤：|其中，|答案[:：])', v):
                suspect = True
            if len(v) > 80:
                suspect = True
            if re.match(r'^\d+[、\.]', v):
                suspect = True
            if re.match(r'^[\-\–\—]', v):
                suspect = True
            if re.search(r'方法(是|：|。)|\(\s*\)|score|z-score|Z-score', v):
                suspect = True

            if suspect:
                q['text'] = v.strip()
                del items[i]
                # if this moved text contains parenthesized answer, extract
                letters2 = extract_paren_letters(q['text'])
                if letters2 and (not q.get('answer')):
                    if is_multiple:
                        q['answer'] = sorted(list({l for l in letters2}))
                    else:
                        q['answer'] = letters2[0]
                    q['text'] = clean_paren_keep_brackets(q['text'])
                break

    # 4) normalize/merge non-standard option keys
    new_items = []
    for k, v in items:
        key = (k or '').upper()
        val = (v or '').strip()
        if key not in allowed_keys:
            # fix cases like 'P' + 'ower' -> 'Power'
            if val and val[0].islower():
                val = key + val
            # merge into previous allowed option if exists
            if new_items:
                last_k, last_v = new_items[-1]
                new_items[-1] = (last_k, (last_v + ' ' + val).strip())
            else:
                # no previous: attach as A
                new_items.append(('A', val))
        else:
            new_items.append((key, val))

    # 5) clean parentheses answers inside option texts as well (remove letters inside)
    cleaned_items = []
    for k, v in new_items:
        v2 = clean_paren_keep_brackets(v)
        cleaned_items.append((k, v2))

    q['options'] = [{'key': k, 'text': v} for k, v in cleaned_items]

    # 6) ensure answer format
    if is_multiple:
        if q.get('answer') is None:
            q['answer'] = []
        elif isinstance(q['answer'], list):
            q['answer'] = sorted(list({a.upper() for a in q['answer']}))
        else:
            # string -> list
            letters = re.findall(r'[A-Za-z]', str(q['answer']))
            q['answer'] = sorted(list({l.upper() for l in letters}))
    else:
        if q.get('answer') is None:
            q['answer'] = None
        elif isinstance(q['answer'], list):
            q['answer'] = q['answer'][0].upper() if q['answer'] else None
        else:
            q['answer'] = str(q['answer']).upper()


# process singles
for q in data.get('single', []):
    process_question(q, allowed_keys=allowed_single_keys, is_multiple=False)

# process multiple
for q in data.get('multiple', []):
    process_question(q, allowed_keys=allowed_single_keys, is_multiple=True)

# write back
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print('cleaned parsed_questions.json')
