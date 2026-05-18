import os
import json
from fpdf import FPDF
from collections import defaultdict
import re

def clean_text(text):
    """Limpa o texto para evitar caracteres que o PDF básico não suporta."""
    if not text:
        return ""
    # Remove tags HTML caso existam
    text = re.sub('<[^<]+?>', '', text)
    # Substitui caracteres comuns de aspas e travessões que quebram o latin-1
    replacements = {
        '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
        '\u2013': '-', '\u2014': '-', '\u2026': '...',
        '\u00a0': ' ', '\u2022': '*', '\u20ac': 'EUR'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Converte para latin-1 ignorando o que sobrar de incompatível
    return text.encode('latin-1', 'ignore').decode('latin-1')

def run():
    # Caminhos relativos ao local do script
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    corpus_dir = os.path.join(base_dir, "backend", "data", "dehon_corpus")
    output_dir = os.path.join(base_dir, "output", "correspondencias_pdf")
    
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(corpus_dir):
        print(f"ERRO: Pasta do acervo não encontrada em: {corpus_dir}")
        return

    # Agrupar cartas por ano
    cartas_por_ano = defaultdict(list)
    total_processados = 0
    total_ignorados = 0

    print("--- Iniciando Processamento Filtrado ---")
    
    arquivos = [f for f in os.listdir(corpus_dir) if f.startswith("COR-") and f.endswith(".json")]
    
    for filename in arquivos:
        try:
            with open(os.path.join(corpus_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                ps = data.get("prosearch", {})
                
                # BUSCA DE TEXTO EM MÚLTIPLOS NÍVEIS
                texto_principal = data.get("content", {}).get("text", "")
                texto_prosearch = ps.get("content", "")
                texto_ref = data.get("documentRef", {}).get("prosearch", {}).get("content", "")
                
                # Escolhe o maior texto disponível
                textos = [texto_principal, texto_prosearch, texto_ref]
                texto_final = max(textos, key=len) if textos else ""
                
                # FILTRO CRÍTICO: Se o texto for apenas o cabeçalho (curto demais), ignora
                # Cartas reais costumam ter mais de 150-200 caracteres de transcrição
                if len(texto_final.strip()) < 150:
                    total_ignorados += 1
                    continue
                
                data["texto_extraido"] = texto_final
                ano = ps.get("year") or data.get("documentRef", {}).get("prosearch", {}).get("year", "Desconhecido")
                cartas_por_ano[str(ano)].append(data)
                total_processados += 1
        except Exception as e:
            print(f"  Erro ao processar {filename}: {e}")

    print(f"Cartas com conteúdo real encontradas: {total_processados}")
    print(f"Documentos ignorados (sem transcrição no original): {total_ignorados}")

    # Gerar os PDFs
    for ano in sorted(cartas_por_ano.keys()):
        cartas = cartas_por_ano[ano]
        print(f"Gerando PDF: Correspondencias_{ano}.pdf")
        
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        for carta in cartas:
            ps = carta.get("prosearch", {})
            titulo = ps.get("title")
            if not titulo or titulo == "null" or titulo == "Sem Título":
                receivers = ps.get("receivers", [])
                authors = ps.get("authors", [])
                if authors and receivers:
                    titulo = f"{authors[0]} para {receivers[0]}"
                else:
                    titulo = ps.get("dehonquote") or "Correspondência"
            
            data_doc = ps.get("date") or "Data desconhecida"
            dest_list = ps.get("receivers", [])
            destinatario = ps.get("receiver") or ps.get("destinatario") or (dest_list[0] if isinstance(dest_list, list) and dest_list else "Não informado")
            texto = carta["texto_extraido"]

            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.multi_cell(0, 10, clean_text(titulo))
            
            pdf.set_font("Arial", 'I', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, clean_text(f"Data: {data_doc} | Destinatário: {destinatario}"), ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, clean_text(texto))
            
            pdf.ln(10)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 5, clean_text(f"ID: {carta.get('document', 'N/A')}"), ln=True, align='R')

        try:
            pdf.output(os.path.join(output_dir, f"Correspondencias_{ano}.pdf"))
        except Exception as e:
            print(f"Erro ao salvar PDF do ano {ano}: {e}")

    print("\n--- Processo Concluído! ---")
    print(f"Seus arquivos PDF estão prontos na pasta: {output_dir}")

if __name__ == "__main__":
    run()
