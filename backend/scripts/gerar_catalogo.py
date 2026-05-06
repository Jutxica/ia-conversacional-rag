import os
import json
from collections import defaultdict

def run():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    corpus_dir = os.path.join(base_dir, "backend", "data", "dehon_corpus")
    output_file = os.path.join(base_dir, "catalogo_dehon.html")
    
    if not os.path.exists(corpus_dir):
        print(f"Erro: Pasta {corpus_dir} não encontrada.")
        return

    catalog = defaultdict(list)
    print("Mapeando acervo...")

    arquivos = [f for f in os.listdir(corpus_dir) if f.endswith(".json")]
    
    for filename in arquivos:
        try:
            with open(os.path.join(corpus_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                ps = data.get("prosearch", {})
                if not ps and "documentRef" in data:
                    ps = data["documentRef"].get("prosearch", {})
                
                doc_id = data.get("document") or data.get("name") or filename.replace(".json", "")
                ano = ps.get("year") or "Desconhecido"
                titulo = ps.get("title") or doc_id
                
                # Verifica se tem conteúdo real
                has_text = len(data.get("content", {}).get("text", "")) > 200 or len(ps.get("content", "")) > 200
                
                # Link direto para o PDF oficial (Padrão sugerido pelo usuário)
                link = f"https://www.dehondocsoriginals.org/pdf/{doc_id}.pdf"
                
                catalog[str(ano)].append({
                    "id": doc_id,
                    "title": titulo,
                    "has_text": has_text,
                    "link": link
                })
        except:
            continue

    # Gerar HTML com design Premium
    html_header = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Catálogo DehonDocs | Utxica</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
        <style>
            :root {{
                --primary: #3498db;
                --bg: #0f172a;
                --card: #1e293b;
                --text: #f8fafc;
            }}
            body {{ 
                font-family: 'Inter', sans-serif; 
                background: var(--bg); 
                color: var(--text);
                padding: 40px; 
                line-height: 1.6;
            }}
            header {{ text-align: center; margin-bottom: 50px; }}
            h1 {{ font-weight: 600; font-size: 2.5rem; margin-bottom: 10px; background: linear-gradient(to right, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .credits {{ font-size: 0.9rem; color: #94a3b8; font-style: italic; }}
            .stats {{ margin-top: 10px; font-size: 1rem; color: #38bdf8; font-weight: bold; }}
            
            .ano-section {{ background: var(--card); margin-bottom: 30px; padding: 25px; border-radius: 12px; border: 1px solid #334155; }}
            .ano-title {{ font-size: 1.5rem; border-left: 4px solid var(--primary); padding-left: 15px; margin-bottom: 20px; }}
            
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; padding: 12px; border-bottom: 2px solid #334155; color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; }}
            td {{ padding: 15px 12px; border-bottom: 1px solid #334155; }}
            tr:hover {{ background: #334155; }}
            
            .status-ok {{ color: #4ade80; font-size: 0.85rem; background: rgba(74, 222, 128, 0.1); padding: 4px 8px; border-radius: 4px; }}
            .status-empty {{ color: #fbbf24; font-size: 0.85rem; background: rgba(251, 191, 36, 0.1); padding: 4px 8px; border-radius: 4px; }}
            
            .btn-download {{ 
                display: inline-block;
                background: var(--primary);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 0.85rem;
                font-weight: 600;
                transition: all 0.3s;
            }}
            .btn-download:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3); }}
        </style>
    </head>
    <body>
        <header>
            <h1>Acervo Digital Dehoniano</h1>
            <p class="credits">feito por Utxica, usa com moderração.</p>
            <p class="stats">Total de {len(arquivos)} documentos mapeados</p>
        </header>
    """
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_header)

        for ano in sorted(catalog.keys()):
            f.write(f'<div class="ano-section"><h2 class="ano-title">Ano {ano}</h2>')
            f.write('<table><tr><th>Título / ID</th><th>Transcrição</th><th>Ação</th></tr>')
            for item in sorted(catalog[ano], key=lambda x: x['id']):
                status = '<span class="status-ok">Disponível</span>' if item["has_text"] else '<span class="status-empty">Apenas Imagem</span>'
                f.write(f'<tr><td>{item["title"]}<br><small style="color:gray">{item["id"]}</small></td>')
                f.write(f'<td>{status}</td>')
                f.write(f'<td><a href="{item["link"]}" target="_blank" class="btn-download">📄 Baixar PDF</a></td></tr>')
            f.write('</table></div>')

        f.write("</body></html>")

    print(f"Catálogo gerado com sucesso: {output_file}")

if __name__ == "__main__":
    run()
