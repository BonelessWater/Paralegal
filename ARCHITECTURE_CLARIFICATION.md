# Architecture Clarification
## Database vs API Server Data Flow

**Created**: October 26, 2025  
**Purpose**: Clarify separation of concerns between PostgreSQL and API Server

---

## 🎯 Data Separation

### PostgreSQL Database
**Purpose**: Legal document storage and research
**Schema**: `legal_data` (7 tables), `datasets` (2 tables)
**Contains**:
- Legal documents (cases, reports, settlements)
- Morgan & Morgan case files
- Kaggle training datasets
- Law firms, attorneys, topics

**Used By**:
- Legal Researcher Agent (queries similar cases)
- Evidence Sorter Agent (training data)
- RAG system (embeddings from full_text)
- Intelligent Scraper (stores scraped cases)

**Access Method**:
```python
from AMD_server.ml_pipeline.data_loader import DataLoader
loader = DataLoader(host="134.199.202.8", db="paralegal_db")
docs = loader.load_morgan_documents()
```

---

### API Server (FastAPI)
**Purpose**: Task management and workflow orchestration
**Storage**: In-memory dictionaries (for hackathon demo)
**Contains**:
- Tasks (pending → processing → approval → sent)
- Agent status and metrics
- Performance statistics
- Real-time system state

**Used By**:
- React frontend (task management UI)
- Background task processor
- Agent orchestration
- System monitoring

**Access Method**:
```typescript
// Frontend
import { getTasks, approveTask } from './services/api';
const tasks = await getTasks({ status: 'awaiting_approval' });
```

---

## 🔄 Complete Data Flow

### Scenario: Legal Research Task

1. **Frontend** → User creates task
   ```
   POST /tasks/ingest
   {
     "source": "email",
     "content": "Find slip and fall cases with broken wrist"
   }
   ```

2. **API Server** → Stores task in memory
   ```python
   task = Task(id=uuid4(), status='pending', ...)
   tasks_db[task_id] = task
   ```

3. **Background Processor** → Classifies and routes
   ```python
   agent_id = classify_task(content)  # → 'legal_researcher'
   agent = agents_db['legal_researcher']['instance']
   ```

4. **Legal Researcher Agent** → Triggers intelligent scraper
   ```python
   if agent_id == 'legal_researcher' and intelligent_scraper:
       result = await intelligent_scraper.research_question_async(content)
   ```

5. **Intelligent Scraper** → Queries CourtListener API
   ```python
   # 100 concurrent workers scrape 10.6M opinions
   cases = scraper.search_cases(queries)  # 41.7 cases/sec
   ```

6. **Intelligent Scraper** → (Optional) Stores in PostgreSQL
   ```python
   # Store scraped cases for future reference
   for case in cases:
       db.insert_document(case)
   ```

7. **API Server** → Updates task with AI response
   ```python
   task.ai_response = format_research_results(cases)
   task.status = 'awaiting_approval'
   ```

8. **Frontend** → Shows AI response in Approval Queue
   ```
   GET /tasks?status=awaiting_approval
   ```

9. **Human** → Reviews and approves
   ```
   POST /tasks/{id}/approve
   {"approved": true, "send_immediately": true}
   ```

10. **API Server** → Marks task as sent
    ```python
    task.status = 'sent'
    task.metadata['sent_at'] = datetime.now()
    ```

---

## 📊 Data Ownership Matrix

| Data Type | Storage | Persistence | Purpose |
|-----------|---------|-------------|---------|
| **Legal Documents** | PostgreSQL | Permanent | Research database |
| **Scraped Cases** | PostgreSQL (optional) | Permanent | Build knowledge base |
| **Tasks** | In-Memory (API) | Session-only | Demo workflow |
| **Agent Metrics** | In-Memory (API) | Session-only | Real-time stats |
| **Frontend State** | Browser | Session-only | UI state |

---

## 🚀 Why This Architecture?

### For Hackathon Demo:
✅ **Fast to build** - No complex database schema for tasks
✅ **Easy to test** - Just restart API server to reset
✅ **Real-time** - In-memory is instant
✅ **Stateless** - Each demo starts fresh

### For Production (Future):
- Move tasks to PostgreSQL (new `workflow` schema)
- Add task persistence and history
- Add user authentication
- Add audit logging
- Keep same API interface!

---

## 🔍 Key Insight

**The API Server is the "brain" that orchestrates**:
- Task management (in-memory)
- Agent coordination (4 specialists)
- Database queries (legal research)
- Intelligent scraping (CourtListener)
- Frontend communication (REST API)

**The PostgreSQL Database is the "library" that stores**:
- Legal knowledge (cases, precedents)
- Training data (Kaggle datasets)
- Historical cases (Morgan & Morgan files)

**They work together but serve different purposes!**

---

## ✅ Summary

Your current architecture is **CORRECT and OPTIMAL** for the hackathon:

1. **PostgreSQL** = Legal document storage (permanent)
2. **API Server** = Task workflow management (demo/temporary)
3. **Frontend** = User interface (connects to API)
4. **Intelligent Scraper** = Research engine (uses CourtListener API + optionally stores in PostgreSQL)

No changes needed to the database or API server design! ✨
