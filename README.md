# BI Chatbot

An intelligent chatbot that allows end-users to query Business Intelligence (BI) data in natural language.  
The system converts user questions into SQL queries, executes them against a database, and returns the results either as text or as visualizations (tables, charts, etc.).

## Features
- Natural Language Processing (NLP) to parse user questions
- Translation dictionary mapping business terms to database schema
- Automatic SQL query generation
- Database connector supporting multiple DB engines
- Result processing (raw + processed output)
- Visualization support (text, table, chart)

## Tech Stack
- Backend: Python (FastAPI / Flask planned)
- Database: SQLite (initial), extendable to MySQL/PostgreSQL
- ORM: SQLAlchemy
- Visualization: matplotlib / plotly (planned)
