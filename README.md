# Arcleo Assistant

A Streamlit question-answering app for the e-commerce architecture specification. It retrieves relevant passages from a local Chroma vector store and asks Google Gemini to answer using those passages, with section citations.

## Features

- Answers questions grounded in `source/ecommerce_architecture_spec.md`.
- Splits the Markdown specification into chunks and indexes them with Google embeddings.
- Stores vectors in a persistent local Chroma database (`chroma_db/`).
- Retrieves up to four relevant passages and generates a concise answer with Gemini.
- Shows source sections, elapsed answer time, suggested questions, and a downloadable chat transcript.

## Requirements

- Python 3.10 or newer
- A Google AI API key that can access the models configured in `rag.py`
- The project files arranged as shown below

```text
project/
├── app.py
├── rag.py
├── .env
└── source/
    └── ecommerce_architecture_spec.md
```

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   On Windows, activate it with `.venv\\Scripts\\activate`.

2. Install the Python packages:

   ```bash
   pip install streamlit python-dotenv langchain-chroma langchain-core langchain-google-genai langchain-text-splitters
   ```

3. Create a `.env` file beside `app.py` and add your API key:

   ```dotenv
   GOOGLE_API_KEY=your_google_ai_api_key
   ```

4. Put the architecture specification at `source/ecommerce_architecture_spec.md`.

## Run the app

From the project directory, run:

```bash
streamlit run app.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) to open in your browser.