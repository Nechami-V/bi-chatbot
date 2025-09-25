# BI Chatbot with Advanced AI Capabilities

A smart chatbot that allows users to ask questions in natural language and receive answers from BI data.  
The system uses advanced AI models to understand questions, generate SQL queries, and analyze results.

---

## 🚀 Main Features

### 🤖 Advanced AI Capabilities
- Understands questions in natural Hebrew
- Automatic SQL query generation
- Intelligent results analysis
- Generates clear and natural answers
- Advanced user intent recognition

### 📊 Data Analysis
- Supports a wide range of queries
- Automatic detection of tables and fields
- Automatic database schema analysis
- Identifies relationships between tables

### 📈 Visualization
- Automatic suggestions for suitable charts
- Organized table display
- Line, bar, and scatter charts
- Data-type–adaptive visualizations

---

## 🛠️ Technologies

| Area        | Technology |
|-------------|------------|
| **Backend** | Python 3.8+, FastAPI, SQLAlchemy (ORM), OpenAI API |
| **Database** | SQLite (default), MySQL, PostgreSQL |
| **Visualization** | Plotly, Matplotlib |

---

## ⚡ Quick Installation

1. **Clone the project**
   ```bash
   git clone https://github.com/Nechami-V/bi-chatbot
   cd bi-chatbot
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   cp .env.example .env
   # Edit the .env file and add your OpenAI API key
   ```

4. **Initialize the database**
   ```bash
   python -m app.db.init_db
   ```

5. **Run the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 🧪 Running Tests

Run all tests:
```bash
pytest
```

Test the system with sample data:
```bash
python test_smart_ai.py
```

---

## 📚 Example Queries

- "Show me all customers"
- "What is the monthly revenue?"
- "Who is the customer with the highest sales?"
- "Display sales by month"
- "What is the most popular product?"
- "Compare sales across quarters"

---

## 📄 License

This project is licensed under the **MIT License**.
