<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
- **Implementation Plan**: [specs/001-linebot-us-stock-news/plan.md](specs/001-linebot-us-stock-news/plan.md)
- **Research Findings**: [specs/001-linebot-us-stock-news/research.md](specs/001-linebot-us-stock-news/research.md)
- **Data Models**: [specs/001-linebot-us-stock-news/data-model.md](specs/001-linebot-us-stock-news/data-model.md)
- **API Contracts**: [specs/001-linebot-us-stock-news/contracts/](specs/001-linebot-us-stock-news/contracts/)
- **Quick Start**: [specs/001-linebot-us-stock-news/quickstart.md](specs/001-linebot-us-stock-news/quickstart.md)
- **Feature Specification**: [specs/001-linebot-us-stock-news/spec.md](specs/001-linebot-us-stock-news/spec.md)
- **Project Constitution**: [.specify/memory/constitution.md](.specify/memory/constitution.md)

**Technical Stack**: Python 3.11+ | FastAPI | async/await | HMAC-SHA256 Signature Verification | Yahoo Finance API | Google News RSS | SQLite/PostgreSQL

**Key Principles**: Reliability (HMAC verification, error handling), Responsive Performance (<300ms indices, <2s queries), Financial Data Security (TLS 1.2+, no stale cache), Test-First (≥80% coverage), Modular Architecture (DI, handlers/services/integrations separation)
<!-- SPECKIT END -->
