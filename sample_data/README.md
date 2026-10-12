# Sample Data

This directory contains sample data for testing the AUTOSAR HLD Assistant.

## Synthetic Test Document

The test suite uses a **synthetic AUTOSAR BCM HLD document** generated
programmatically by `tests/conftest.py`. It contains:

- Realistic AUTOSAR software component descriptions (LightingManager, DoorLockController, etc.)
- Interface and port definitions
- Signal definitions with CAN IDs
- BSW stack configuration (MCAL, COM, OS, DCM, DEM, NVM)
- Functional flow sequences
- Known limitation statements

This synthetic data is used for all automated tests. No confidential automotive documents are required.

## Using Your Own Documents

You can upload your own AUTOSAR HLD PDF documents through the application's
Upload & Process tab. The system supports any text-based PDF.

**Note:** Scanned/image-based PDFs require OCR preprocessing (e.g., Adobe Acrobat,
Tesseract, or ABBYY FineReader) before they can be processed by this tool.

## Provided Sample PDF

`Automotive_Engineering_AI_Project_Case_Studies.pdf` – Located in the project
root. Upload this via the web interface to test the full pipeline with
real automotive engineering content.
