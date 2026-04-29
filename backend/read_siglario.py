import os
from pypdf import PdfReader

def read_pdf():
    docs_dir = "docs"
    files = os.listdir(docs_dir)
    target = [f for f in files if f.startswith("Sigl") and f.endswith(".pdf")][0]
    reader = PdfReader(os.path.join(docs_dir, target))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

if __name__ == "__main__":
    content = read_pdf()
    with open("siglario_content.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Success")
