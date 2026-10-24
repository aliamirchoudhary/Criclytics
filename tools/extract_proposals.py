from zipfile import ZipFile
from pathlib import Path
import re

from criclytics_app.paths import PROJECT_ROOT
paths = [PROJECT_ROOT / 'docs/history/Criclytics_Project_Proposal.docx', PROJECT_ROOT / 'docs/history/Iteration_1.docx']
for p in paths:
    print('FILE', p)
    with ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    toks = re.findall(r'<w:t[^>]*>(.*?)</w:t>', xml)
    lines = []
    current = []
    for t in toks:
        if t.strip():
            current.append(t)
        else:
            if current:
                lines.append(' '.join(current))
                current = []
    if current:
        lines.append(' '.join(current))
    for line in lines[:120]:
        print(line)
    print('---\n')
