# US Stock Financial LINE Bot Assistant Constitution

## Core Principles

### I. Reliability & Data Integrity (NON-NEGOTIABLE)
All financial data served to users MUST be accurate, consistent, and up-to-date. No data loss or corruption is acceptable. Every transaction, quote, and portfolio calculation MUST be validated before display. Implement idempotent operations where possible; all state changes MUST be logged and auditable.

### II. Responsive Performance
API response time MUST NOT exceed 2 seconds under normal load; LINE Bot message acknowledgment within 500ms. All user-facing operations optimized for latency. Implement caching strategically for read-heavy financial data; invalidate cache within 5 minutes of market updates. Real-time data feeds (stock prices, portfolio updates) prioritize speed over perfect consistency.

### III. User-Centric Design
Every feature starts with user intent and workflow. UI/UX must be intuitive for non-technical users; financial concepts explained clearly without jargon. Commands and responses optimized for LINE's conversational interface; support both inline buttons and multi-turn dialogues. Accessibility is mandatory—support traditional and simplified Chinese, clear visual hierarchy, keyboard navigation.

### IV. Financial Data Security (NON-NEGOTIABLE)
All sensitive user data (API credentials, portfolio holdings, transaction history) encrypted at rest and in transit using industry-standard protocols. Authentication via OAuth 2.0 or equivalent; no passwords stored in plaintext. Comply with financial data protection regulations. Implement rate limiting and fraud detection. Regular security audits required; vulnerability disclosure process documented.

### V. Test-First Development (NON-NEGOTIABLE)
TDD mandatory for all features: Requirements written → Approval from stakeholder → Tests written → Tests fail → Implement → Tests pass → Refactor. Unit test coverage minimum 80%; integration tests for all market data integrations and user transaction flows. Automated testing gates in CI/CD pipeline prevent untested code from reaching production.

### VI. Clear Documentation & Transparency
All API endpoints, data schemas, and error codes documented with examples. Financial calculations transparent—users can understand exactly how recommendations are generated. README in Traditional Chinese for user-facing features; API documentation in English. Maintain a public changelog of all feature additions and breaking changes.

### VII. Modularity & Extensibility
Core features (market data retrieval, portfolio calculation, alert system) implemented as independent modules. Each module has clear contracts and error boundaries. New integrations (additional brokers, data providers) should be added without modifying existing code. Support plugin architecture for custom strategies and indicators.

## Performance & Reliability Standards

- Stock quote response time: <300ms (90th percentile)
- Portfolio calculation: <1 second for up to 500 holdings
- Message delivery success rate: >99.9%
- Data consistency: No staleness >5 minutes for real-time data
- Uptime SLA: 99.5% (excluding planned maintenance)
- Database backup: Every 6 hours with verified restore testing

## Security & Compliance Requirements

- Encrypt all credentials using AES-256
- TLS 1.2+ for all network communications
- Store user session tokens with 24-hour expiration
- Implement 2FA for account access (if applicable)
- Regular dependency scanning for vulnerabilities
- Comply with Taiwan financial data protection standards
- Third-party integrations (brokers, data providers) must be vetted and sandboxed

## Development Workflow & Quality Gates

- All PRs require code review before merge; security and performance reviews mandatory
- Commit messages must reference task/issue ID and clearly describe changes
- Feature branches follow naming convention: `feature/<issue-id>-<description>`
- Deployment workflow: develop → staging (automated tests) → production (manual approval)
- Post-deployment monitoring: Verify error rates, response times, and user feedback within 1 hour

## Governance

This Constitution supersedes all other development practices and style guides. Every team member is accountable for upholding these principles. 

**Amendment Process**: Proposed amendments must be documented with rationale, impact assessment, and migration plan. Changes to principles require team approval; clarifications to governance require lead engineer sign-off. All amendments logged in version history.

**Versioning**: Semantic versioning (MAJOR.MINOR.PATCH) applied to Constitution. MAJOR bump for principle removals/redefinitions; MINOR for new principle additions; PATCH for clarifications and non-semantic refinements.

**Compliance Review**: Quarterly retrospectives to assess adherence to principles; incident reports analyzed for principle violations.

**Version**: 1.0.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-05-17
