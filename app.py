from flask import Flask, render_template, request, send_file, url_for
import os
import fitz  # PyMuPDF for PDFs
from docx import Document
import re

app = Flask(__name__)

# File storage paths
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
WORD_LIST_FOLDER = "wordlists"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(WORD_LIST_FOLDER, exist_ok=True)

def read_word_list(file_path):
    """Reads a list of words from an uploaded text or CSV file."""
    words = []
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            words = [line.strip() for line in file.readlines()]
    return words

def highlight_text_in_pdf(pdf_path, output_path, keywords):
    """Highlight trigger words in a PDF document."""
    doc = fitz.open(pdf_path)
    for page in doc:
        for word in keywords:
            text_instances = page.search_for(word)
            for inst in text_instances:
                highlight = page.add_highlight_annot(inst)
                highlight.update()
    doc.save(output_path)
    doc.close()

def highlight_text_in_docx(docx_path, output_path, keywords):
    """Highlight trigger words in a Word document."""
    doc = Document(docx_path)

    for para in doc.paragraphs:
        for word in keywords:
            pattern = re.compile(rf"\b{word}\b", re.IGNORECASE)
            if pattern.search(para.text):
                for run in para.runs:
                    if pattern.search(run.text):
                        run.font.highlight_color = 2  # Apply yellow highlight

    doc.save(output_path)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    word_list_file = os.path.join(WORD_LIST_FOLDER, "custom_words.txt")

    if request.method == "POST":
        # Ensure word list is uploaded
        if "word_list" in request.files:
            word_file = request.files["word_list"]
            if word_file.filename:
                word_file.save(word_list_file)
            else:
                return "❌ Please upload a word list before processing documents."

        # Read the updated word list
        trigger_words = read_word_list(word_list_file)

        if not trigger_words:
            return "❌ No words found in the uploaded list. Please check your file."

        # Handle document upload
        if "file" in request.files:
            uploaded_file = request.files["file"]
            if uploaded_file:
                file_name = uploaded_file.filename
                file_ext = file_name.split(".")[-1].lower()
                input_path = os.path.join(UPLOAD_FOLDER, file_name)
                output_path = os.path.join(PROCESSED_FOLDER, "highlighted_" + file_name)

                uploaded_file.save(input_path)

                if file_ext == "pdf":
                    highlight_text_in_pdf(input_path, output_path, trigger_words)
                elif file_ext == "docx":
                    highlight_text_in_docx(input_path, output_path, trigger_words)
                else:
                    return "❌ Unsupported file type. Please upload a PDF or DOCX."

                return f'<a href="{url_for("download_file", filename="highlighted_" + file_name)}" class="btn btn-success mt-2">Download Highlighted File</a>'

    return render_template("index.html")

@app.route("/download/<filename>")
def download_file(filename):
    return send_file(os.path.join(PROCESSED_FOLDER, filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
