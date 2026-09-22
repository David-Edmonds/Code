"""Verify the publicly reviewed Tableau project snapshot with the standard library."""
from pathlib import Path
import hashlib
import re
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
workbook = root / 'Startup-Operations-Expanded.twbx'
assert hashlib.sha256(workbook.read_bytes()).hexdigest() == '06b8a746dc9f715c9e752a5f9bd805f5b001e5a546b82b6478836451606cffba', 'Workbook differs from reviewed public snapshot'
with zipfile.ZipFile(workbook) as package:
    assert package.testzip() is None
    xml = package.read(next(n for n in package.namelist() if n.endswith('.twb')))
    document = ET.fromstring(xml)
    assert len(document.findall('./dashboards/dashboard')) == 7
    assert len(document.findall('./worksheets/worksheet')) == 70
    assert sum(n.endswith('.hyper') for n in package.namelist()) == 2
    assert not re.search(rb'C:[\\/]|Users[\\/]', xml), 'Local path in workbook'
assert len(list((root / 'Expanded-Screenshots').glob('*.jpg'))) == 7
for url in re.findall(r'(?:src|href)="([^"]+)"', (root / 'index.html').read_text(encoding='utf-8')):
    if not url.startswith(('#', 'https://', 'http://')):
        assert (root / url).is_file(), f'Broken gallery link: {url}'
print('Startup Operations: workbook integrity, 7 dashboards, 70 worksheets, 2 extracts and gallery links verified.')
