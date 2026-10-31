# AutoGen AI Customer Support Automation

An AI-powered customer support proof of concept built using **Microsoft AutoGen, Retrieval-Augmented Generation (RAG), FAISS, OpenAI, SQLite, and Streamlit**.

The system demonstrates how multiple AI agents can collaborate to classify customer complaints, retrieve relevant knowledge-base policies, generate responses, and prepare structured support tickets for human review.

## Project Objectives

- Automate initial customer-support complaint processing.
- Improve response consistency using knowledge-base retrieval.
- Coordinate specialized AI agents through AutoGen.
- Support human approval, revision, and rejection of AI-generated responses.
- Maintain ticket records, delivery history, and audit trails.
- Validate functionality through automated regression testing.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| Microsoft AutoGen | Multi-agent orchestration |
| OpenAI GPT-4o-mini | Agent reasoning and response generation |
| OpenAI text-embedding-3-small | Knowledge-base embeddings |
| FAISS | Semantic vector search |
| SQLite | Ticket persistence and audit history |
| Streamlit | Human review and ticket management UI |
| Pytest | Automated regression testing |

## System Architecture

```text
Customer Complaint
       |
       v
AutoGen Multi-Agent Workflow
       |
       +-- Customer Query Agent
       |       Classifies complaint
       |
       +-- Knowledge Base Agent
       |       Retrieves policy evidence
       |       using FAISS RAG
       |
       +-- Resolution Agent
       |       Generates proposed response
       |
       +-- Log Agent
               Produces structured ticket data
       |
       v
Validation and Ticket Creation
       |
       v
SQLite Database
       |
       v
Human Review Console
       |
       +-- Approve
       +-- Revise -> AI Response Revision
       +-- Reject
       |
       v
Approved Response
       |
       v
Simulated Delivery
       |
       v
Ticket Lifecycle and Audit Trail
```

## Key Features

### 1. Multi-Agent Customer Support

Four specialized AutoGen agents process customer complaints in a controlled sequence:

1. Customer Query Agent
2. Knowledge Base Agent
3. Resolution Agent
4. Log Agent

The support service validates the expected execution order before creating a ticket.

### 2. Retrieval-Augmented Generation

The RAG pipeline loads Markdown policy documents, splits them into chunks, generates embeddings, and stores vectors in FAISS.

The sample knowledge base includes:

- Shipping policy
- Refund policy
- Account and login support
- Product FAQs
- Billing policy

The sample policies are fictional and intended for demonstration.

### 3. Human-in-the-Loop Review

Reviewers can:

- Approve proposed AI responses.
- Request revisions with reviewer notes.
- Reject responses with recorded reasons.
- Review revised AI responses before approval.

Review actions are recorded in the ticket audit history.

### 4. Ticket Lifecycle Management

Supported ticket states include:

- Pending
- Escalated
- Resolved
- Closed

Ticket status transitions are validated and recorded in SQLite.

### 5. Simulated Customer Response Delivery

Approved responses can be processed through a simulated delivery workflow.

The system records delivery receipts and delivery history without actually sending customer messages.

**Important:** Simulated delivery is not proof that a customer received a response.

### 6. Audit Trail

The application records events including ticket creation, review decisions, AI revisions, simulated delivery, and ticket status changes.

## Project Structure

```text
agents/             AutoGen agent definitions
rag/                RAG ingestion and retrieval
knowledge_base/     Sample support policies
workflows/          Multi-agent and revision workflows
services/           Ticket, review, delivery, lifecycle logic
database/           SQLite schema and connections
ui/                 Streamlit interfaces
tests/              Automated and development tests
reports/            Regression test reports
data/               Generated local data (Git ignored)
logs/               Runtime logs (Git ignored)
```

## Installation

### Prerequisites

- Python 3.12
- OpenAI API key

### Create a virtual environment

```powershell
python -m venv .venv
```

### Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Configure environment variables

Create a local `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key
```

Never commit real API keys or credentials.

### Knowledge-Base Setup

The FAISS index is generated locally and excluded from Git.

Before using live knowledge-base retrieval, build the index from the sample policy documents using the project's RAG ingestion modules.

## Running Automated Tests

Run the regression tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ticket_creation_pytest.py tests\test_human_review_pytest.py tests\test_delivery_pytest.py tests\test_lifecycle_pytest.py tests\test_database_isolation.py tests\test_rag_retrieval_pytest.py tests\test_agent_workflow_pytest.py tests\test_workflow_integration_pytest.py tests\test_agent_handoff_pytest.py tests\test_support_service_pytest.py -v
```

### Verified Regression Results

| Metric | Result |
|---|---|
| Automated tests | 49 |
| Passed | 49 |
| Failed | 0 |
| Execution time | 1.64 seconds |
| Real FAISS retrieval Hit Rate@5 | 5/5 evaluation queries |

JUnit XML report: `reports/full_regression_results.xml`

The 49-test regression suite includes mocked components and does not constitute a full live OpenAI end-to-end evaluation.

## Current Limitations

This is an educational proof of concept, not a production-ready customer support platform.

- Customer delivery is simulated.
- Sample policy documents are fictional.
- Authentication and role-based authorization require production implementation.
- Resolution and closure require stronger real-world verification.
- Real API integration, deployment, and security testing require further validation.
- The complete live application startup and FAISS index initialization procedures should be documented before deployment.

## Future Enhancements

- Real email or messaging delivery integrations.
- Role-based reviewer authentication.
- Customer-support API integrations.
- Production deployment using Docker.
- Expanded RAG evaluation and response-quality metrics.
- Monitoring, observability, and operational dashboards.
- CI/CD regression testing with GitHub Actions.

## Project Status

**Proof of concept implemented — 49 automated regression tests passing.**

Built as part of independent learning and practical exploration of Generative AI architecture, multi-agent systems, RAG, and human-in-the-loop automation.
