# FiCo Kaşif Backend

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_key
   PINECONE_API_KEY=your_key
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=fico_kasif
   ```
5. Run the server: `uvicorn main:app --reload`

## API Endpoints
- `POST /v1/query`: RAG-based query
- `POST /v1/feedback`: User feedback
- `GET /v1/sources/{id}`: Source document retrieval
