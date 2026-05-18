import os
import hashlib
from collections import defaultdict

DIR = "ia-conversacional-rag/data/dehon_corpus_full"

def get_stats():
    files = [f for f in os.listdir(DIR) if f.endswith(".md")]
    print(f"Total files: {len(files)}")
    
    empty_files = []
    content_hashes = defaultdict(list)
    
    for f in files:
        path = os.path.join(DIR, f)
        size = os.path.getsize(path)
        
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            
            # Simple check for "empty" or default message
            if "Conteúdo não disponível" in content or len(content.strip()) < 100:
                empty_files.append(f)
            
            # Hash content to find duplicates (ignoring header)
            if "---" in content:
                main_content = content.split("---", 1)[1].strip()
                if main_content:
                    h = hashlib.md5(main_content.encode()).hexdigest()
                    content_hashes[h].append(f)
                else:
                    empty_files.append(f)

    print(f"Empty or placeholder files: {len(empty_files)}")
    
    duplicates = {h: flist for h, flist in content_hashes.items() if len(flist) > 1}
    print(f"Duplicate content groups: {len(duplicates)}")
    if duplicates:
        print("Sample duplicates:")
        for h, flist in list(duplicates.items())[:5]:
            print(f"  {h}: {flist}")

if __name__ == "__main__":
    if os.path.exists(DIR):
        get_stats()
    else:
        print(f"Directory {DIR} not found.")
