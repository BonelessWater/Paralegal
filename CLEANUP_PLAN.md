# Repository Cleanup Plan
## Paralegal AI - Code Audit & Cleanup

**Date**: October 26, 2025  
**Purpose**: Remove unused files, update documentation, organize codebase  
**Status**: 🔄 IN PROGRESS

---

## 📋 Audit Summary

### Current State
- **Total Python files**: 166
- **Total Documentation files**: 78
- **Core system files**: 6 (intelligent scraping system)
- **Legacy/Unused files**: ~150+ (to be cleaned)

---

## 🗂️ Files to KEEP (Production)

### Core Intelligent Scraping System (KEEP - PRODUCTION READY)
```
✅ AMD_server/ml_pipeline/intelligent_scraper.py      # Multi-mode scraper
✅ AMD_server/ml_pipeline/query_generator.py          # LLM query generation
✅ AMD_server/ml_pipeline/auto_integration.py         # RAG integration
✅ AMD_server/ml_pipeline/orchestrator.py             # Hyper-parallelized coordinator
✅ AMD_server/ml_pipeline/rag_embeddings.py           # FAISS embeddings
✅ AMD_server/ml_pipeline/data_loader.py              # Database integration
```

### Supporting Infrastructure (KEEP)
```
✅ AMD_server/ml_pipeline/__init__.py                 # Package init
✅ AMD_server/ml_pipeline/quick_access_check.py       # CourtListener test
✅ AMD_server/ml_pipeline/check_access.py             # Comprehensive access check
✅ AMD_server/scraper/database.py                     # Database connection
✅ AMD_server/scraper/setup_database.py               # DB setup script
```

### Configuration Files (KEEP)
```
✅ .env                                               # Environment variables
✅ requirements.txt                                   # Python dependencies
✅ test_complete_system.sh                           # Test suite
✅ quick_fix_dependencies.sh                         # Dependency installer
✅ README.md                                         # Main README
✅ SYSTEM_DOCUMENTATION.md                           # Complete docs (NEW)
```

### Essential Documentation (KEEP & UPDATE)
```
✅ docs/INTELLIGENT_SCRAPING_SYSTEM.md               # System architecture
✅ docs/FAISS_EXECUTION_GUIDE.md                     # RAG setup
✅ docs/DATABASE_DOCUMENTATION.md                    # DB schema
✅ docs/MODEL_SETUP_GUIDE.md                         # Model setup
✅ docs/GPU_OPTIMIZATION_GUIDE.md                    # AMD MI300X optimization
```

---

## 🗑️ Files to DELETE (Unused/Obsolete)

### Duplicate/Obsolete Scrapers (DELETE)
```
❌ AMD_server/scraper/scrape.py                      # Old LexisNexis scraper
❌ AMD_server/scraper/load_morgan_files.py           # Superseded by data_loader
❌ AMD_server/scraper/test_scraper.py                # Old tests
❌ AMD_server/load_morgan_files.py                   # Duplicate
❌ scraper/load_kaggle_datasets.py                   # Moved to AMD_server
```

### Obsolete Audio Processing (DELETE - Not in use)
```
❌ AMD_server/ml_pipeline/audio/                     # Entire audio folder
   - whisper_local.py
   - whisper_api.py
   - whisper_parallel.py
   - transcribe_local.py
   - transcribe_api.py
   - audio_loader.py
   - gpu_resource_manager.py
   - gpu_monitor.py
   - test_one_file.py
```

### Obsolete Email Processing (DELETE - Not in use)
```
❌ AMD_server/ml_pipeline/emailer/                   # Entire emailer folder
   - email_classifier.py
   - email_loader.py
   - email_processor.py
   - test_email.py
```

### Obsolete OCR (DELETE - Not in use)
```
❌ AMD_server/ml_pipeline/ocr/                       # Entire OCR folder
   - ocr_processor.py
   - image_loader.py
   - test_ocr.py
❌ AMD_server/OCR.py                                 # Standalone OCR
```

### Old Test Files (DELETE - Superseded by test_complete_system.sh)
```
❌ AMD_server/test_rag_simple.py
❌ AMD_server/test_rag_agent.py
❌ AMD_server/test_complete_system.py
❌ AMD_server/test_agents.py
❌ AMD_server/ml_pipeline/test_db_connection.py
❌ AMD_server/ml_pipeline/diagnose_cache.py
❌ AMD_server/ml_pipeline/inspect_database.py
❌ AMD_server/scraper/test_database.py
```

### Obsolete ML Files (DELETE - Not in current system)
```
❌ AMD_server/ml_pipeline/train.py                   # Old training script
❌ AMD_server/ml_pipeline/train_test_split.py
❌ AMD_server/ml_pipeline/ml_inference.py
❌ AMD_server/ml_pipeline/feature_engineering.py
❌ AMD_server/ml_pipeline/benchmark_faiss.py
❌ AMD_server/ml_pipeline/rag_embeddings_local.py    # Duplicate
```

### Obsolete Structured Data (DELETE - Not in current system)
```
❌ AMD_server/ml_pipeline/structured/                # Entire structured folder
   - settlement_predictor.py
   - case_matcher.py
   - feature_engineering.py
   - data_loader.py
   - test_structured.py
```

### Old Agent System (DELETE - Superseded by intelligent scraping)
```
❌ AMD_server/agents/                                # Old agent implementations
   - client_communication_agent.py
   - legal_researcher_agent.py
   - records_wrangler_agent.py
   - evidence_sorter_agent.py
```

### Old ADK Experiments (DELETE - Not in production)
```
❌ AMD_server/ADK/                                   # Entire ADK folder
   - researcher.py
   - test_system.py
   - run_saul_completion.py
   - benchmark.py
   - a2a_agents/
   - basic_agents/
```

### Backend APIs (DELETE - Not used in current system)
```
❌ backend/APIs/                                     # Entire backend folder
   - email/
   - text/
   - call/
   - db/
   - AMD/ADK/
   - AMD/OCR/
```

### Old Process Files (DELETE)
```
❌ AMD_server/process_files.py
❌ AMD_server/server.py                              # Old server
```

### Obsolete Documentation (DELETE/ARCHIVE)
```
❌ docs/TEAMMATE_HANDOFF.md                          # Outdated
❌ docs/AUDIO_TRANSCRIPTION_COMPARISON.md            # Not in use
❌ docs/QUICKSTART_PARALLEL_WHISPER.md               # Not in use
❌ docs/QUICKSTART_LOCAL_WHISPER.md                  # Not in use
❌ docs/LOCAL_WHISPER_SETUP.md                       # Not in use
❌ docs/MILVUS_AMD_FEASIBILITY.md                    # Evaluated, not used
❌ docs/IMPLEMENTATION_PLAN_REVISED.md               # Planning doc
❌ docs/GOOGLE_ADK_REAL_INTEGRATION.md               # Not in use
❌ docs/FINAL_ARCHITECTURE_DECISION.md               # Superseded
❌ docs/TEAMMATE_QUICKSTART.md                       # Outdated
❌ docs/CURRENT_EMBEDDING_STATUS.md                  # Outdated status
```

### Setup Scripts (DELETE - Not needed)
```
❌ AMD_server/scraper/config.ini.example             # Not used
❌ AMD_server/scraper/setup.ps1                      # Windows script
❌ run_transcription.sh                              # Audio not in use
❌ fix_and_run.sh                                    # Obsolete
❌ quick_start_faiss.sh                              # Superseded
```

---

## ✏️ Files to UPDATE

### README.md (UPDATE - Needs current info)
```
📝 README.md
   - Update with current architecture
   - Add performance metrics
   - Link to SYSTEM_DOCUMENTATION.md
   - Add quick start guide
   - Remove obsolete sections
```

### Documentation to Update
```
📝 docs/INTELLIGENT_SCRAPING_SYSTEM.md
   - Update with latest performance metrics
   - Add test results
   - Update architecture diagram

📝 docs/FAISS_EXECUTION_GUIDE.md
   - Clarify current status (caching only)
   - Add future integration plans

📝 docs/DATABASE_DOCUMENTATION.md
   - Update with current schema
   - Add intelligent scraping tables
```

---

## 📦 New Folder Structure (After Cleanup)

```
Paralegal/
├── .env                              # Environment config
├── .gitignore                        # Git ignore
├── README.md                         # ✏️ UPDATE - Main project README
├── SYSTEM_DOCUMENTATION.md           # ✅ NEW - Complete docs
├── requirements.txt                  # Python dependencies
├── test_complete_system.sh           # Test suite
├── quick_fix_dependencies.sh         # Dependency installer
│
├── AMD_server/
│   └── ml_pipeline/                  # Core intelligent scraping system
│       ├── __init__.py
│       ├── intelligent_scraper.py    # ✅ KEEP - Multi-mode scraper
│       ├── query_generator.py        # ✅ KEEP - LLM query gen
│       ├── auto_integration.py       # ✅ KEEP - RAG integration
│       ├── orchestrator.py           # ✅ KEEP - Coordinator
│       ├── rag_embeddings.py         # ✅ KEEP - FAISS system
│       ├── data_loader.py            # ✅ KEEP - Database
│       ├── quick_access_check.py     # ✅ KEEP - CourtListener test
│       ├── check_access.py           # ✅ KEEP - Access check
│       └── data/                     # Data storage
│           ├── cache/                # Scraped cases
│           └── integration_logs/     # Metrics
│
├── docs/                             # Documentation
│   ├── INTELLIGENT_SCRAPING_SYSTEM.md  # ✅ KEEP - Architecture
│   ├── FAISS_EXECUTION_GUIDE.md        # ✅ KEEP - RAG guide
│   ├── DATABASE_DOCUMENTATION.md       # ✅ KEEP - DB schema
│   ├── MODEL_SETUP_GUIDE.md            # ✅ KEEP - Model setup
│   ├── GPU_OPTIMIZATION_GUIDE.md       # ✅ KEEP - GPU guide
│   └── ARCHITECTURE_OVERVIEW.md        # ✅ KEEP - Overview
│
└── archive/                          # ❌ MOVE old files here (optional)
    ├── old_agents/
    ├── old_scrapers/
    ├── audio_processing/
    └── email_processing/
```

---

## 🚀 Cleanup Execution Plan

### Phase 1: Documentation (NOW)
- [x] Create SYSTEM_DOCUMENTATION.md
- [ ] Update README.md
- [ ] Update INTELLIGENT_SCRAPING_SYSTEM.md
- [ ] Archive obsolete docs

### Phase 2: Delete Unused Code (NEXT)
- [ ] Delete audio processing folder
- [ ] Delete email processing folder
- [ ] Delete OCR folder
- [ ] Delete old agents
- [ ] Delete old ADK experiments
- [ ] Delete backend APIs
- [ ] Delete structured data folder

### Phase 3: Clean Tests (NEXT)
- [ ] Delete old test files
- [ ] Keep only test_complete_system.sh
- [ ] Verify all tests pass

### Phase 4: Final Organization (LAST)
- [ ] Organize remaining files
- [ ] Update .gitignore
- [ ] Commit cleanup
- [ ] Tag release (v2.0.0)

---

## 📊 Cleanup Impact

### Before Cleanup
- Total files: ~250+
- Python files: 166
- Doc files: 78
- Folder depth: 6 levels
- Confusion: HIGH

### After Cleanup
- Total files: ~30-40
- Python files: ~15
- Doc files: ~8
- Folder depth: 3 levels
- Clarity: HIGH ✨

### Estimated Size Reduction
- **Code reduction**: ~90% (150 files → 15 files)
- **Doc reduction**: ~90% (78 files → 8 files)
- **Total reduction**: ~85% (250 files → 40 files)

---

## ✅ Verification Checklist

After cleanup, verify:
- [ ] `./test_complete_system.sh` passes all tests
- [ ] All imports work correctly
- [ ] No broken documentation links
- [ ] README.md is current and accurate
- [ ] .env has all required variables
- [ ] Git repository is clean

---

**Next Steps**: Execute Phase 1 (Documentation Updates)
