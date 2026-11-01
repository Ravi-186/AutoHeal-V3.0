import re

with open('web/templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

pages = re.findall(r'id=["\'](page\w+)["\']', text)
print("Pages found in index.html:", pages)

nav_tabs = re.findall(r'data-page=["\'](\w+)["\']', text)
print("Nav tabs:", nav_tabs)
