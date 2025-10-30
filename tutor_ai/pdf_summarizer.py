# pdf_summarizer.py
import PyPDF2
import re
from transformers import T5Tokenizer, T5ForConditionalGeneration, pipeline

# Charger le modèle T5 (ou un modèle plus puissant si disponible)
model_path = "tutor_ai/models/booksum_t5_final"  # ton modèle local
tokenizer = T5Tokenizer.from_pretrained(model_path)
model = T5ForConditionalGeneration.from_pretrained(model_path)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=-1)  # CPU = -1

# --------------------------
# Nettoyage et segmentation
# --------------------------
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # espaces multiples → un seul
    text = text.replace('•', '\n•')  # garder les listes
    return text.strip()

def split_sections(text):
    """
    Séparer le texte par titres basés sur majuscules ou mots clés (Introduction, MVC, etc.)
    """
    # On utilise une regex pour détecter les titres (en majuscules ou suivis de ':')
    pattern = re.compile(r'([A-Z][A-Z\s]{2,}|[A-Z][a-z]+:)', re.MULTILINE)
    splits = pattern.split(text)
    
    # Recomposer sections (titre + contenu)
    sections = []
    for i in range(1, len(splits), 2):
        title = splits[i].strip()
        content = splits[i+1].strip() if i+1 < len(splits) else ""
        if content:
            sections.append((title, content))
    return sections

# --------------------------
# Résumé hiérarchique
# --------------------------
def summarize_text(text, max_chunk=1500, max_tokens=400):
    """
    Résumer un texte long en plusieurs étapes si nécessaire
    """
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
    partial_summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_new_tokens=max_tokens, do_sample=False)[0]['summary_text'].strip()
        partial_summaries.append(summary)

    # Fusionner les résumés partiels si nécessaire
    while len(partial_summaries) > 1:
        new_summaries = []
        for i in range(0, len(partial_summaries), 3):
            block = " ".join(partial_summaries[i:i+3])
            summary = summarizer(block, max_new_tokens=max_tokens, do_sample=False)[0]['summary_text'].strip()
            new_summaries.append(summary)
        partial_summaries = new_summaries

    return partial_summaries[0] if partial_summaries else "Résumé non disponible"

# --------------------------
# Résumer un PDF
# --------------------------
def summarize_pdf_file(file_path):
    # Lire le PDF
    reader = PyPDF2.PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"

    # Nettoyer le texte
    full_text = clean_text(full_text)

    # Découper en sections
    sections = split_sections(full_text)

    # Résumer chaque section
    section_summaries = []
    for title, content in sections:
        summary = summarize_text(content)
        section_summaries.append(f"{title}:\n{summary}\n")

    # Résumé final
    final_summary = "\n".join(section_summaries)
    return final_summary

# --------------------------
# Test rapide
# --------------------------
if __name__ == "__main__":
    pdf_path = r"C:\Users\yosry\OneDrive\Bureau\HubEducator\media\lesson_resources\PowerPoint_Presentation_AIvAZ1r.pdf"
    summary = summarize_pdf_file(pdf_path)
    print("=== Résumé du PDF ===\n")
    print(summary)
