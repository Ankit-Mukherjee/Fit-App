# FitFlow Coach

A personalized AI-powered fitness coaching application that provides custom macro recommendations and workout advice.

## Features

- Personalized macro planning based on user profile and goals
- AI-powered workout recommendations and advice
- Vector database-powered note-taking system for progress tracking
- Semantic search capabilities for finding relevant past advice
- Retrieval-Augmented Generation (RAG) for context-aware AI responses
- Modern, responsive React frontend

## Tech Stack

### Backend
- Python
- FastAPI
- Astra DB (with NVIDIA AI vector search)
- LangFlow for AI workflow
- Python-dotenv for environment management

### Frontend
- React
- Vite
- React Markdown
- Modern CSS with responsive design

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Ankit-Mukherjee/Fit-App.git
cd Fit-App
```

2. Set up environment variables:
Create a `.env` file in the root directory with:
```
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_KEYSPACE=your_keyspace
LANGFLOW_API_KEY=your_langflow_key
```

3. Install backend dependencies:
```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

5. Run the development servers:

Backend:
```bash
uvicorn app:app --reload
```

Frontend:
```bash
cd frontend
npm run dev
```

## Features

### Profile Management
- User profile creation and management
- Customizable fitness goals
- Activity level tracking

### Macro Planning
- AI-generated macro recommendations
- Personalized nutrition advice
- Save and track macro plans

### Workout Advice
- AI-powered workout recommendations
- Context-aware responses using RAG
- Vector similarity search for relevant past advice

### Note Taking
- Save workout advice and macro plans
- Automatic vectorization for semantic search
- Build personalized knowledge base

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.