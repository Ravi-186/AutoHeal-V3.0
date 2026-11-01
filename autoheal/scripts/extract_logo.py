import docx
import re

doc = docx.Document(r'C:\Users\bobba\Downloads\Project DocumentAI SOC.docx')
p0 = doc.paragraphs[0]
xml = p0._p.xml
matches = re.findall(r'embed=["\'](\w+)["\']', xml)
print("Embed IDs in p0:", matches)
if matches:
    r_id = matches[0]
    part = doc.part.related_parts[r_id]
    with open('AutoHeal_Documentation/university_logo.png', 'wb') as f:
        f.write(part.blob)
    print("Successfully extracted university_logo.png! Size:", len(part.blob))
