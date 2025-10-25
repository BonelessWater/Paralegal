# Paralegal AI Documentation

**Team**: BonelessWater  
**Hackathon**: AI Legal Tender (October 25, 2025)

---

## 📚 Documentation Index

### Core Documentation

#### 1. [DATABASE_DOCUMENTATION.md](docs/DATABASE_DOCUMENTATION.md)
**Complete PostgreSQL database reference**
- Database schema (all tables and fields)
- Morgan & Morgan case files (54 documents, 4 cases)
- Kaggle datasets catalog (11 datasets, 74 GB)
- SQL queries and examples
- Maintenance and troubleshooting

**When to use**: Database setup, queries, understanding data structure

---

#### 2. [MODEL_SETUP_GUIDE.md](docs/MODEL_SETUP_GUIDE.md)
**Model selection and configuration**
- Recommended legal LLM models
- Download and deployment instructions
- vLLM server configuration
- Performance optimization

**When to use**: Choosing and deploying AI models

---

#### 3. [ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)
**System design and architecture**
- High-level system design
- Component relationships
- Agent workflows
- Technology stack

**When to use**: Understanding system design, making architectural decisions

---

#### 4. [AGENT_TRAINING_OPTIMIZATION.md](docs/AGENT_TRAINING_OPTIMIZATION.md)
**Training strategies and performance tuning**
- Agent pipeline optimization
- Training best practices
- Performance metrics
- Quality evaluation

**When to use**: Optimizing agent performance, implementing training pipelines

---

## 🚀 Quick Links by Task

### Setup & Installation
- **Database Setup**: [DATABASE_DOCUMENTATION.md](docs/DATABASE_DOCUMENTATION.md) - Connection info, schema creation
- **Model Setup**: [MODEL_SETUP_GUIDE.md](docs/MODEL_SETUP_GUIDE.md) - Download and deploy models
- **System Architecture**: [ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) - Overall system design

### Data & Training
- **Morgan & Morgan Cases**: [DATABASE_DOCUMENTATION.md#morgan--morgan-case-files](docs/DATABASE_DOCUMENTATION.md#morgan--morgan-case-files)
- **Kaggle Datasets**: [DATABASE_DOCUMENTATION.md#dataset-catalog](docs/DATABASE_DOCUMENTATION.md#dataset-catalog)
- **Agent Training**: [AGENT_TRAINING_OPTIMIZATION.md](docs/AGENT_TRAINING_OPTIMIZATION.md)

### Operations
- **Database Queries**: [DATABASE_DOCUMENTATION.md#common-queries](docs/DATABASE_DOCUMENTATION.md#common-queries)
- **Troubleshooting**: [DATABASE_DOCUMENTATION.md#maintenance--troubleshooting](docs/DATABASE_DOCUMENTATION.md#maintenance--troubleshooting)
- **Performance Tuning**: [AGENT_TRAINING_OPTIMIZATION.md](docs/AGENT_TRAINING_OPTIMIZATION.md)

---

## 📊 Data Assets Summary

### PostgreSQL Database
- **54 Morgan & Morgan case documents** (police reports, settlements, audio recordings)
- **11 Kaggle datasets** (814,812 files, 74 GB)
- **4 specialist AI agents** (Client Comm, Legal Research, Evidence Sorting, Records)

### Server Information
- **Host**: 134.199.202.8 (AMD MI300X)
- **Database**: paralegal_db (PostgreSQL 16)
- **User**: paralegal_user
- **Password**: hackathon2024

---

## 🎯 Documentation Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| DATABASE_DOCUMENTATION.md | ✅ Current (v2.0) | Oct 25, 2025 |
| MODEL_SETUP_GUIDE.md | ✅ Current | Oct 25, 2025 |
| ARCHITECTURE_OVERVIEW.md | ✅ Current | Oct 25, 2025 |
| AGENT_TRAINING_OPTIMIZATION.md | ✅ Current | Oct 25, 2025 |

**Total Documentation**: 4 core files (redundant files removed)

---

## 📝 Recent Updates (v2.0 - Oct 25, 2025)

### Database Documentation
- ✅ Fixed all table schemas to match actual implementation
- ✅ Corrected column names (document_id, url, court, law_firm_id, etc.)
- ✅ Added Morgan & Morgan case files documentation (54 documents)
- ✅ Updated Kaggle datasets to 11 successful downloads
- ✅ Removed failed datasets from catalog

### Documentation Cleanup
- ✅ Removed 8 outdated/redundant documentation files
- ✅ Consolidated to 4 core documents
- ✅ Created this documentation index

---

## 🔗 External Resources

- **GitHub Repository**: https://github.com/BonelessWater/Paralegal
- **AMD Server**: ssh amd-knights@134.199.202.8
- **Setup Scripts**: `~/Paralegal/AMD_server/setup/`
- **Configuration**: `~/Paralegal/.env`

---

**For questions or issues, refer to the specific documentation files above.**
