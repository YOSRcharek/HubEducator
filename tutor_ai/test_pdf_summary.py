from pdf_summarizer import summarize_pdf_file

pdf_path = r"C:\Users\yosry\OneDrive\Bureau\HubEducator\media\lesson_resources\PowerPoint_Presentation_AIvAZ1r.pdf"

with open(pdf_path, "rb") as f:
    summary = summarize_pdf_file(f)

print("=== Résumé du PDF ===")
print(summary)
