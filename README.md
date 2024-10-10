# PDF Editor

**!! This document was generated using ChatGPT.**

This application is a versatile tool for editing PDF files, built using Streamlit and various Python libraries. With this app, you can:

- Merge multiple PDFs
- Rotate pages in a PDF
- Reorder pages in a PDF
- Delete or extract specific pages from a PDF

## Features

1. **Merge PDFs**: Combine multiple PDF files into one, and select the order of merging.
2. **Rotate Pages**: Rotate selected pages within a PDF by 90, 180, or 270 degrees.
3. **Reorder Pages**: Rearrange pages in a PDF by selecting which pages to move and where to insert them.
4. **Delete or Extract Pages**: Either delete selected pages or extract them into a new PDF.

## Installation

### Prerequisites

- Python 3.12 or higher
- The following Python libraries (as defined in `pyproject.toml`):
  - `streamlit >= 1.39.0`
  - `pypdf >= 5.0.1`
  - `pdf2image >= 1.17.0`

You can install these dependencies using [Poetry](https://python-poetry.org/). First, ensure you have Poetry installed, then run:

```bash
poetry install
```

If you prefer using `pip`, you can manually install the dependencies:

```bash
pip install streamlit pypdf pdf2image
```

### Poppler Installation (Required for `pdf2image`)

The `pdf2image` library requires the Poppler utility to convert PDFs to images. Installation steps vary depending on your operating system.

## Running the Application

Once all dependencies are installed, you can run the app using the `activation_local.bat` file provided for Windows users. This script will automatically launch the Streamlit app using Poetry. 

To start the application, simply double-click the `activation_local.bat` file, which contains the following command:

```bash
poetry run streamlit run app.py
```

This will open a new browser window where you can interact with the PDF editor.

## Usage

- Select an action from the sidebar:
  - **Merge PDFs**: Upload multiple PDFs and select their merging order.
  - **Rotate Pages**: Rotate specific pages in a PDF by selecting them from thumbnails.
  - **Reorder Pages**: Select pages and move them to a new position in the PDF.
  - **Delete or Extract Pages**: Remove pages from the PDF or extract them into a separate file.
- Upload one or more PDF files.
- After performing the desired action, download the modified PDF file.
