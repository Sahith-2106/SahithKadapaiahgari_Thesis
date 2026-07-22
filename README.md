# TEI Conversion Pipeline for Historical Vocational Documents

This project presents a custom pipeline for converting scanned historical vocational training documents—specifically from the German Democratic Republic (GDR) into semantically rich **TEI XML** representations. The pipeline integrates OCR, layout detection, and semantic tagging, tailored for a unique corpus of structured job descriptions preserved by the **Bundesinstitut für Berufsbildung (BIBB)**.

## 📜 Thesis Overview

The goal of this thesis is to design, develop, and evaluate an end-to-end system that:
- Performs OCR on scanned historical documents
- Detects layout regions (headings, tables, paragraphs)
- Extracts structured data and maps it to TEI-compliant XML
- Handles semantic features such as **Berufstitel**, **Berufsnummern**, and training descriptions

> 📄 Full documentation: [Thesis PDF](https://github.com/Sahith-2106/SahithKadapaiahgari_Thesis/blob/main/Documentation/SaiVenkataSahithReddyKadapaiahgari_22220197807282025_032752.PDF)

---

## 🧠 Features

- 🧾 **OCR + Layout Detection** using deep learning-based segmentation (PaddleDetection)
- 📦 **Structured Region Extraction** from multi-column, complex-layout GDR documents
- 🏷️ **TEI P5 XML Generation** with semantically tagged metadata
- 🧪 **Evaluation Metrics**: Precision, Recall, F1-Score, Accuracy

---

## 📁 Project Structure

```plaintext
.
├── data/                   # Sample input scans and TEI outputs
├── Trained Models/         # Layout detection model checkpoints
├── src/                    # Core source code (OCR, TEI generation, etc.)
│   ├── Paddle-Pytesseract.py
│   ├── Json-Xml.py/
│   └── evaluation.py/
└── README.md
