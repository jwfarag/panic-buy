# Infrastructure TODOs

## Hybrid Local/Cloud Execution

### Priority: Medium (after core pipeline works locally)

### Goal
Allow users to run the system on a laptop for daily use, while offloading resource-intensive tasks to cloud infrastructure.

### Tasks

- [ ] **Storage abstraction layer**
  - Unified interface for local filesystem and cloud object storage
  - Automatic sync between local cache and cloud
  - Configurable threshold for cloud offload (e.g., >10GB to S3)

- [ ] **Compute abstraction layer**
  - Task router that decides local vs cloud execution
  - Support for:
    - Local: multiprocessing
    - AWS: SageMaker jobs, Lambda
    - GCP: Vertex AI, Cloud Functions
    - Azure: ML Studio, Functions

- [ ] **Training offload**
  - Package training job as container
  - Submit to cloud ML service
  - Pull trained model artifacts back to local

- [ ] **Data tiering**
  - Hot data (recent): local
  - Warm data (30-90 days): local or cloud
  - Cold data (90+ days): cloud only
  - Automatic promotion/demotion based on access patterns

- [ ] **Cost controls**
  - Monthly budget limits
  - Alerts at 50%, 80%, 100% of budget
  - Automatic fallback to local-only mode if budget exceeded

- [ ] **Sync mechanism**
  - Bidirectional sync for models and processed data
  - Conflict resolution (cloud wins for models, merge for data)
  - Offline mode support (queue cloud tasks for later)

### Implementation Notes
- Start with AWS (most common), add GCP/Azure later
- Use boto3/s3fs for AWS storage abstraction
- Consider Metaflow or similar for compute orchestration

---

## Future Features (Not Currently Planned)

### Real-time Alerting
- Email/Slack/SMS notifications
- Alert filtering and deduplication
- Would require streaming architecture

### Execution Integration
- Paper trading first
- Broker API integration (Alpaca, IBKR)
- Requires extensive risk controls

### Web Dashboard
- Real-time opportunity display
- Historical performance tracking
- Configuration UI

---

## Technical Debt

### To Address Before Production
- [ ] Add comprehensive error handling
- [ ] Implement retry logic for all external APIs
- [ ] Add request caching for news sources
- [ ] Implement proper logging throughout
- [ ] Add input validation for all public interfaces
- [ ] Create database schema (currently file-based)

### Nice to Have
- [ ] Add type hints throughout codebase
- [ ] Set up pre-commit hooks
- [ ] Add documentation generation (Sphinx)
- [ ] Create CLI interface for manual operations
