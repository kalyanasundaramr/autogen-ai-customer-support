# AutoGen AI Customer Support Desk

**Multi-Agent AI Customer Support Automation | RAG | Human-in-the-Loop | Docker**

An AI-powered customer support proof of concept built using Microsoft AutoGen, OpenAI, FAISS, SQLite, Streamlit, and Docker.

The application coordinates four specialized AI agents to classify complaints, retrieve relevant support policies, generate proposed responses, and create structured tickets for human review.

**Live Demo:** https://support.kalyanr.tech

The demo is password-protected. Access credentials are provided privately to authorized reviewers.

## Project Objectives

- Automate initial customer complaint analysis and classification.
- Retrieve relevant knowledge-base evidence using RAG.
- Generate policy-grounded customer support responses.
- Escalate high-risk complaints for human review.
- Support approval, revision, and rejection workflows.
- Maintain persistent tickets and audit history.
- Deploy the application securely using Docker and HTTPS.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Application development |
| Microsoft AutoGen | Multi-agent orchestration |
| OpenAI GPT-4o-mini | Agent reasoning and response generation |
| OpenAI text-embedding-3-small | Knowledge-base embeddings |
| FAISS | Vector similarity search |
| SQLite | Ticket, review, and audit persistence |
| Streamlit | Interactive support dashboard |
| Pytest | Automated regression testing |
| Docker Compose | Containerized deployment |
| Nginx | HTTPS reverse proxy |
| Let's Encrypt | TLS certificates |
| Hostinger VPS | Application hosting |

## System Architecture

```text
Customer Complaint
       |
       v
Streamlit Support Dashboard
       |
       v
AutoGen Multi-Agent Workflow
       |
       +-- Customer Query Agent
       |      Complaint classification
       |      Urgency and sentiment analysis
       |
       +-- Knowledge Base Agent
       |      FAISS retrieval
       |      Support policy evidence
       |
       +-- Resolution Agent
       |      AI-generated proposed response
       |
       +-- Log Agent
              Structured ticket data
       |
       v
Validation and Escalation Engine
       |
       +-- Normal complaint --> Pending
       |
       +-- High-risk complaint --> Escalated
       |
       v
SQLite Ticket Database
       |
       v
Human-in-the-Loop Review
       |
       +-- Approve
       +-- Revise --> AI response revision
       +-- Reject
       |
       v
Simulated Response Delivery
       |
       v
Ticket Lifecycle and Audit History
```

The application runs inside Docker on a Hostinger VPS. Nginx provides HTTPS routing and Basic Authentication.

## Key Features

### 1. AutoGen Multi-Agent Workflow

Four specialized agents collaborate sequentially:

1. **Customer Query Agent:** Classifies complaints, urgency, sentiment, and escalation indicators.
2. **Knowledge Base Agent:** Retrieves relevant policy evidence using FAISS.
3. **Resolution Agent:** Generates proposed customer responses grounded in retrieved information.
4. **Log Agent:** Produces structured ticket information for validation and persistence.

### 2. Retrieval-Augmented Generation

The application uses five sample policy documents:

- Shipping policy
- Refund policy
- Account and login support
- Product FAQs
- Billing policy

Documents are chunked, embedded using `text-embedding-3-small`, and indexed with FAISS.

The policies are fictional and intended for educational demonstration.

### 3. Escalation Engine

Deterministic escalation rules identify complaints requiring additional attention, including:

- High urgency
- Very angry sentiment
- Legal threats
- Billing or payment disputes
- Fraud and account-security concerns
- Unsupported knowledge-base requests
- Significantly delayed deliveries

Escalated tickets are routed to human review.

### 4. Human-in-the-Loop Review

Reviewers can approve, revise, or reject proposed AI responses.

Revision requests can trigger AI-assisted response regeneration. Review decisions and associated notes are recorded for auditability.

### 5. Streamlit Support Dashboard

The application provides five tabs:

| Tab | Function |
|---|---|
| Dashboard | Support ticket overview |
| New Complaint | Submit complaints for AI processing |
| Tickets | Review ticket information and status |
| Human Review | Approve, revise, or reject responses |
| Audit & Reports | Inspect recorded support events |

### 6. Ticket Lifecycle and Audit

The application manages ticket states including Pending, Escalated, Resolved, and Closed.

Ticket creation, review decisions, revisions, simulated delivery, and lifecycle changes are recorded in SQLite.

### 7. Simulated Customer Response Delivery

Approved responses can be processed through a simulated delivery workflow.

**No real customer messages are sent.** Delivery receipts are demonstration records rather than evidence of actual customer receipt.

## Project Structure

```text
agents/              AutoGen agents
rag/                 Embeddings, indexing, retrieval
knowledge_base/      Sample support policies
workflows/           Agent orchestration and revisions
services/            Support, escalation, review, delivery
database/            SQLite database operations
ui/                  Streamlit dashboard
tests/               Automated tests
reports/             Generated test reports
data/                Runtime SQLite and FAISS files
Dockerfile           Container build
docker-compose.yml   Container orchestration
.env.example         Environment configuration template
```

Runtime data and credentials are excluded from Git.

## Local Installation

### Prerequisites

- Python 3.12
- OpenAI API key

Clone the repository:

```bash
git clone https://github.com/kalyanasundaramr/autogen-ai-customer-support.git
cd autogen-ai-customer-support
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Build the FAISS index from the sample policy documents using the project's RAG ingestion modules before processing complaints.

The generated FAISS index is excluded from Git, so a fresh clone requires index initialization.

### Run the Streamlit Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/support_dashboard.py
```

Open the local Streamlit URL shown in the terminal.

## Docker Deployment

The application supports Docker Compose deployment.

```bash
docker compose build
docker compose up -d
```

The production VPS configuration binds Streamlit to:

`127.0.0.1:8503`

Nginx proxies the application through:

https://support.kalyanr.tech

The deployment uses:

- Docker container restart policy: `unless-stopped`
- Persistent `./data:/app/data` volume
- Environment variables loaded from `.env`
- Docker container health checks
- Nginx HTTPS reverse proxy
- Let's Encrypt TLS certificate
- Nginx Basic Authentication

The published Compose configuration may require adjustment to bind the host port to localhost on a new server.

## Automated Testing

Run the test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

**Latest confirmed regression suite:** 71 automated tests passing.

Testing covers agent orchestration, RAG retrieval, ticket creation, escalation, human review, simulated delivery, database isolation, and lifecycle management.

The suite includes mocked components and does not replace full live-model evaluation.

## Deployment Validation

The deployed proof of concept has been manually verified for:

- Docker container health
- HTTPS access and password authentication
- Customer complaint submission
- Multi-agent ticket creation
- Delayed-delivery escalation
- Human approval
- Audit history
- SQLite persistence after Docker restart

## Current Limitations

This project is an educational proof of concept rather than a production-ready customer support platform.

- Sample policies are fictional.
- Customer response delivery is simulated.
- Nginx Basic Authentication protects the demo but does not provide application-level role-based authorization.
- Live-model accuracy and policy compliance require broader evaluation.
- Production usage would require stronger privacy controls, monitoring, backups, and security testing.
- The FAISS index must be initialized or transferred when deploying a fresh clone.

## Future Enhancements

- Real email and messaging integrations
- Role-based access control
- External CRM and ticketing integration
- Automated backup and recovery
- Expanded RAG evaluation
- Observability and performance monitoring
- CI/CD automation

## Project Status

**Buildathon proof of concept completed and deployed.**

The project demonstrates multi-agent orchestration, retrieval-augmented generation, deterministic escalation, human-in-the-loop review, persistent ticket management, and containerized deployment.

Developed as part of independent practical learning in Generative AI and Agentic AI.

**GitHub:** https://github.com/kalyanasundaramr/autogen-ai-customer-support

**Live Demo:** https://support.kalyanr.tech
