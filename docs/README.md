# Documentation Index

Welcome to the AI Shopping Assistant Lab documentation. This guide helps you navigate the comprehensive documentation for Week 02 enhancements.

---

## 📚 Documentation Structure

```
docs/
├── README.md               ← You are here
├── ARCHITECTURE.md         # System design + Mermaid diagrams
├── TECHNICAL.md            # Implementation deep-dive
└── QUICK_REFERENCE.md      # Cheat sheet + commands

../CHANGELOG.md             # Version history + release notes
../README.md                # Project overview + quick start
```

---

## 🗺️ Documentation Navigator

### For New Users

**Start here:**
1. 📖 [README.md](../README.md) - Project overview and quick start
2. 📋 [CHANGELOG.md](../CHANGELOG.md) - What's new in Week 02
3. 🚀 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Fast setup guide

### For Developers

**Implementation details:**
1. 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md) - System design and component architecture
2. 🔧 [TECHNICAL.md](TECHNICAL.md) - Code-level implementation details
3. 📊 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Code snippets and commands

### For DevOps/SRE

**Operations focus:**
1. 🐳 [README.md](../README.md#running-with-docker-compose) - Docker deployment
2. 📈 [ARCHITECTURE.md](ARCHITECTURE.md#performance-characteristics) - Performance metrics
3. 🔧 [TECHNICAL.md](TECHNICAL.md#performance-optimization) - Tuning guide

### For Data Scientists

**RAG pipeline focus:**
1. 🔍 [ARCHITECTURE.md](ARCHITECTURE.md#hybrid-search-architecture) - Search strategy
2. 📊 [TECHNICAL.md](TECHNICAL.md#hybrid-search-implementation) - RRF algorithm details
3. 🧪 [TECHNICAL.md](TECHNICAL.md#testing-strategies) - Evaluation with RAGAS

---

## 📖 Document Descriptions

### [CHANGELOG.md](../CHANGELOG.md)
**Purpose**: Track all changes between versions  
**Audience**: All users  
**Key Sections**:
- Week 02 feature additions
- Breaking changes
- Migration guide
- Dependency updates

**When to read**: 
- Before upgrading to Week 02
- Understanding what changed
- Migration planning

---

### [ARCHITECTURE.md](ARCHITECTURE.md)
**Purpose**: High-level system design and architecture  
**Audience**: Architects, senior engineers, technical leads  
**Key Sections**:
- System architecture diagrams (Mermaid)
- Component interactions
- Data flow sequences
- Deployment topology
- Technology stack decisions

**Contains**:
- 8 Mermaid diagrams
- Component descriptions
- Design decisions rationale
- Scalability considerations

**When to read**:
- Understanding system design
- Planning integrations
- Architectural reviews
- Onboarding new engineers

---

### [TECHNICAL.md](TECHNICAL.md)
**Purpose**: Deep implementation details and code-level docs  
**Audience**: Engineers, data scientists  
**Key Sections**:
- Hybrid search implementation (RRF algorithm)
- Instructor integration (structured outputs)
- Prompt management (Jinja2 templates)
- Database schema (Qdrant configuration)
- Performance optimization
- Testing strategies

**Contains**:
- Code snippets with explanations
- Algorithm details and formulas
- Configuration examples
- Troubleshooting guides

**When to read**:
- Implementing features
- Debugging issues
- Performance tuning
- Understanding "how it works"

---

### [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**Purpose**: Fast lookup for common tasks  
**Audience**: All technical users  
**Key Sections**:
- Quick start commands
- Code snippets
- Configuration reference
- Troubleshooting common issues
- Performance benchmarks

**Contains**:
- Copy-paste ready commands
- Common code patterns
- Quick fixes
- Useful shortcuts

**When to read**:
- Setting up environment
- Need quick answers
- Running common operations
- Daily development tasks

---

## 🎯 Quick Links by Topic

### Hybrid Search
- [Architecture Overview](ARCHITECTURE.md#hybrid-search-architecture)
- [Implementation Details](TECHNICAL.md#hybrid-search-implementation)
- [RRF Algorithm Explained](TECHNICAL.md#rrf-algorithm-explained)
- [Weight Tuning Guide](QUICK_REFERENCE.md#rrf-weight-tuning)

### Structured Outputs
- [Architecture](ARCHITECTURE.md#structured-output-architecture)
- [Instructor Integration](TECHNICAL.md#structured-output-with-instructor)
- [Code Snippets](QUICK_REFERENCE.md#structured-output-with-instructor)

### Prompt Management
- [System Design](ARCHITECTURE.md#prompt-management-architecture)
- [Implementation](TECHNICAL.md#prompt-management-system)
- [Template Usage](QUICK_REFERENCE.md#prompt-template)

### Citation Grounding
- [Data Flow](ARCHITECTURE.md#rag-pipeline-flow-week-02)
- [Implementation](TECHNICAL.md#citation-and-grounding)
- [API Response](QUICK_REFERENCE.md#api-response-schema)

### Database
- [Collection Schema](TECHNICAL.md#database-schema)
- [Setup Guide](QUICK_REFERENCE.md#qdrant-collection-setup)
- [Indexing Strategy](TECHNICAL.md#indexing-strategy)

### Performance
- [Characteristics](ARCHITECTURE.md#performance-characteristics)
- [Optimization](TECHNICAL.md#performance-optimization)
- [Benchmarks](QUICK_REFERENCE.md#performance-benchmarks)

### Deployment
- [Docker Compose](ARCHITECTURE.md#deployment-architecture)
- [Setup Instructions](../README.md#running-with-docker-compose)
- [Commands](QUICK_REFERENCE.md#docker)

---

## 🔍 Search Guide

### Finding Information

**"How do I...?"** questions:
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) first
- Then [README.md](../README.md) for setup
- Finally [TECHNICAL.md](TECHNICAL.md) for detailed steps

**"Why does...?"** questions:
- Start with [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions
- Then [TECHNICAL.md](TECHNICAL.md) for implementation reasoning

**"What changed...?"** questions:
- Check [CHANGELOG.md](../CHANGELOG.md)
- Compare sections in ARCHITECTURE vs TECHNICAL docs

**"What is...?"** questions:
- [ARCHITECTURE.md](ARCHITECTURE.md) for high-level concepts
- [TECHNICAL.md](TECHNICAL.md) for detailed explanations

---

## 📊 Mermaid Diagrams

All diagrams are in [ARCHITECTURE.md](ARCHITECTURE.md) and render on GitHub:

1. **System Architecture** - Overall system components
2. **RAG Pipeline Flow** - Sequence diagram of full pipeline
3. **Hybrid Search Strategy** - Dense + sparse fusion
4. **Structured Output Flow** - Instructor integration
5. **Prompt Rendering Flow** - Jinja2 template system
6. **Deployment Topology** - Docker network architecture
7. **LangSmith Tracing** - Observability setup
8. **Retrieval Strategy** - RRF fusion visualization

---

## 🛠️ Common Documentation Tasks

### Task: Understand Week 02 Changes
1. Read [CHANGELOG.md](../CHANGELOG.md#week-02---2026-07-05)
2. Review [ARCHITECTURE.md](ARCHITECTURE.md#architecture-evolution)
3. Check [Migration Guide](../CHANGELOG.md#migration-notes)

### Task: Set Up Development Environment
1. Follow [README.md](../README.md#setup)
2. Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md#quick-start)
3. Verify with [Troubleshooting](QUICK_REFERENCE.md#troubleshooting)

### Task: Implement Hybrid Search
1. Understand [Architecture](ARCHITECTURE.md#hybrid-search-architecture)
2. Study [RRF Algorithm](TECHNICAL.md#rrf-algorithm-explained)
3. Copy [Code Snippet](QUICK_REFERENCE.md#hybrid-search-query)
4. Configure [Qdrant Collection](TECHNICAL.md#collection-requirements)

### Task: Debug Performance Issues
1. Check [Latency Breakdown](TECHNICAL.md#latency-breakdown)
2. Review [Optimization Strategies](TECHNICAL.md#optimization-strategies)
3. Compare [Benchmarks](QUICK_REFERENCE.md#performance-benchmarks)

### Task: Customize Prompts
1. Understand [Prompt System](ARCHITECTURE.md#prompt-management-architecture)
2. Learn [Template Syntax](TECHNICAL.md#template-structure)
3. Use [Best Practices](TECHNICAL.md#best-practices)

---

## 📝 Documentation Standards

### Diagram Format
- **Mermaid** for all architecture diagrams (version-controlled, GitHub-rendered)
- Include both high-level and detailed views
- Add legends for complex diagrams

### Code Examples
- Always include context and explanation
- Show complete, runnable examples
- Include error handling where relevant
- Add comments for clarity

### Versioning
- Tag major changes with week numbers
- Use comparison tables for evolution
- Maintain migration guides between versions

### Updates
- Update docs with code changes
- Keep examples in sync with implementation
- Version documentation in git
- Review docs in PRs

---

## 🤝 Contributing to Documentation

### When to Update Docs

✅ **Always update**:
- Adding new features
- Changing APIs or interfaces
- Modifying architecture
- Performance optimizations

⚠️ **Consider updating**:
- Bug fixes (if common issue)
- Configuration changes
- New use cases or patterns

### Which Document to Update

| Change Type | Update |
|-------------|--------|
| New feature | CHANGELOG + ARCHITECTURE + TECHNICAL |
| API change | CHANGELOG + QUICK_REFERENCE |
| Architecture change | ARCHITECTURE + TECHNICAL |
| Bug fix | CHANGELOG (if notable) |
| Performance tuning | TECHNICAL + QUICK_REFERENCE |
| New deployment | ARCHITECTURE + README |

---

## 📧 Getting Help

### Documentation Issues

**Can't find what you need?**
1. Search this index for keywords
2. Use GitHub's file search in `/docs`
3. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md#troubleshooting)

**Documentation unclear?**
- Open an issue describing what's confusing
- Suggest specific improvements

**Missing documentation?**
- Note what's missing in issue
- Reference where it should be added

---

## 📈 Version History

| Version | Date | Changes |
|---------|------|---------|
| Week 02 | 2026-07-05 | Initial comprehensive documentation |
| Week 01 | 2026-06-28 | Basic README only |

---

## 🎓 Learning Path

### Beginner (1-2 hours)
1. [README.md](../README.md) - 15 min
2. [CHANGELOG.md](../CHANGELOG.md) - 15 min
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 30 min
4. Run the application - 30 min

### Intermediate (3-4 hours)
1. [ARCHITECTURE.md](ARCHITECTURE.md) - 60 min
2. Study Mermaid diagrams - 30 min
3. [TECHNICAL.md](TECHNICAL.md) - Sections 1-3 - 60 min
4. Implement a feature change - 60 min

### Advanced (1-2 days)
1. Complete [TECHNICAL.md](TECHNICAL.md) - 3 hours
2. Review all code with docs - 4 hours
3. Performance tuning exercises - 2 hours
4. Contribute improvements - 2+ hours

---

**Last Updated**: 2026-07-05  
**Maintainer**: Suresh Putla
