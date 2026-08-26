# AI Support Agent — RAG & Order Support

A reliable AI support agent built for the Aster & Row ecommerce scenario.

The agent combines Retrieval-Augmented Generation (RAG), order lookup tools, multi-turn conversation handling, safe responses, and evaluation-driven testing.

## Project Overview

This project implements an AI-powered customer support agent for Aster & Row.

The agent is designed to answer customer questions using the supplied knowledge base and mock order data while avoiding unsupported claims and exposing internal information.

### Main Capabilities

- Retrieval-Augmented Generation (RAG) over the supplied knowledge base
- Order lookup using the supplied order data
- Order ID normalization and safe handling of unknown orders
- Multi-turn conversation support
- Source references for policy and product answers
- Safe handling of conflicting or insufficient information
- Protection of internal customer/order fields
- Tool-call tracking and deterministic evaluation
- Automated regression testing

## Technology Stack

- **Language:** Python
- **Agent:** Custom Python support agent
- **RAG:** Retrieval over the supplied knowledge-base documents
- **Order Data:** JSON
- **Testing:** Pytest
- **Version Control:** Git & GitHub

## Architecture

The system follows a simple routing architecture.

```text
                    User
                      |
                      v
              Support Agent
                      |
          +-----------+-----------+
          |                       |
          v                       v
   Policy/Product             Order Question
      Question                     |
          |                        v
          v                  Order Lookup Tool
       RAG Layer                  |
          |                        v
          v                  Order Data (JSON)
 Knowledge Base
          |
          v
   Relevant Sources
          |
          +-----------+
                      |
                      v
                Final Response
 ```

## Project Structure

```text
ai-agent-intern-test/
├── app/
├── data/
├── evaluation/
├── knowledge-base/
├── scripts/
├── tests/
├── README.md
└── requirements.txt
```

## Implementation Details

### 1. Support Agent

The `SupportAgent` is responsible for understanding customer questions and routing them to the appropriate handling flow.

It supports:

- Order-specific questions
- Policy-related questions
- Product and knowledge-base questions
- General customer-support queries
- Multi-turn conversation context

### 2. RAG Pipeline

The RAG pipeline loads the supplied knowledge-base documents, retrieves relevant information, and uses the retrieved content to provide grounded responses.

The system is designed to avoid making unsupported claims when the required information is not available.

### 3. Order Lookup

Order-related queries are handled through the order lookup tool using the supplied mock order data.

The implementation includes:

- Order ID extraction
- Order ID normalization
- Valid order lookup
- Unknown order handling
- Cancelled/returned order handling
- Protection against exposing internal customer/order fields

### 4. Conversation Handling

The agent supports multi-turn conversations by maintaining relevant conversation context and using it when resolving follow-up customer questions.

The conversation flow is designed to:

- Preserve relevant context across turns
- Handle missing information safely
- Ask for clarification when required
- Avoid exposing internal implementation details

### 5. Safety & Reliability

The agent is designed to provide reliable, customer-safe responses while avoiding unsupported or sensitive information.

Key safeguards include:

- Grounding responses in retrieved knowledge-base content
- Avoiding unsupported claims
- Handling insufficient or conflicting information safely
- Protecting internal customer and order information
- Returning deterministic responses for evaluation scenarios

## Testing & Evaluation

The project includes an automated test and evaluation suite using `pytest`.

The tests cover core agent behavior including:

- RAG and knowledge-base retrieval
- Order lookup and tool usage
- Order ID handling and normalization
- Unknown and malformed orders
- Cancelled and returned orders
- Privacy and protection of internal information
- Multi-turn conversation behavior
- Safe handling of insufficient information
- Deterministic agent behavior

### Running the Tests

Run the complete test suite with:

```bash
pytest -q
```

### Final Test Result

The final implementation passes all automated tests:

```text
33 passed
```

This result was achieved after fixing issues identified during development, including response handling, tool-call tracking, order lookup behavior, and safe handling of unknown and cancelled orders.

### Evaluation Approach

The evaluation suite uses deterministic assertions wherever practical so that important behaviors can be verified consistently.

The tests verify not only the final response, but also important internal behavior such as:

- Whether the correct tool was called
- Whether the correct tool arguments were supplied
- Whether an order lookup was performed when required
- Whether the agent asks for missing information
- Whether stale order information is suppressed
- Whether unsupported information is avoided
- Whether sensitive internal information is protected

## Bug Diary

During development, several issues were identified through automated testing and fixed before the final evaluation.

### Bug 1 — SupportAgent Initialization

**Symptom:**  
Tests initially failed because `SupportAgent()` required a `retriever` argument, while the evaluation tests instantiated the agent without one.

**Root Cause:**  
The constructor required a dependency that the test interface expected to be optional.

**Fix:**  
Adjusted the agent initialization so that it could be instantiated using the expected interface while still supporting the required retrieval functionality.

**Regression Test:**  
The complete test suite was rerun after the fix.

---

### Bug 2 — Missing Order Question Handler

**Symptom:**  
Tests failed with:

```text
AttributeError: 'SupportAgent' object has no attribute 'handle_order_question'
```

**Root Cause:**  
The order-specific handling method required by the evaluation tests was not implemented.

**Fix:**  
Implemented `handle_order_question()` to handle missing, valid, cancelled/returned, and unknown order IDs.

**Regression Test:**  
The order-related evaluation tests were rerun and passed.

---

### Bug 3 — Response Metadata Missing

**Symptom:**  
Tests failed because the response did not expose attributes such as `tool_called` and `tool_arguments`.

**Root Cause:**  
The order lookup response returned a plain dictionary instead of the response structure expected by the evaluation tests.

**Fix:**  
Updated the response handling so that tool-call metadata and the customer-facing answer were exposed in the expected response format.

**Regression Test:**  
The order lookup and response-handling tests were rerun successfully.

---

### Bug 4 — Incorrect Unknown-Order Response

**Symptom:**  
The unknown-order test expected the response to communicate that the order could not be found, but the returned message did not match the expected customer-facing wording.

**Root Cause:**  
The lookup result was being returned directly without converting it into the expected customer-safe response.

**Fix:**  
Updated the unknown-order handling to return a clear customer-facing message indicating that the order could not be found.

**Regression Test:**  
The unknown-order evaluation test was rerun and passed.

---

### Final Regression Result

After resolving the above issues, the complete test suite was executed again:

```text
33 passed
```

No test failures remained in the final run.

## Evaluation Results

### Baseline Evaluation

The initial implementation was evaluated against the test and evaluation suite before the final fixes were applied.

The baseline revealed failures in areas including:

- Order lookup behavior
- Response structure and tool-call metadata
- Unknown-order handling
- Cancelled-order handling
- Customer-facing response formatting

The baseline results are documented here to show the improvements made during development.

### Final Evaluation

After implementing the fixes and running the complete regression suite, the final test result was:

```text
33 passed
```

The final implementation successfully passes the complete automated test suite.

### Evaluation Categories

| Category | Final Result |
|---|---|
| Retrieval / RAG | Passing |
| Groundedness & safe responses | Passing |
| Order lookup & tool use | Passing |
| Privacy / internal-data protection | Passing |
| Multi-turn behavior | Passing |
| Regression tests | 33/33 passed |

The evaluation suite uses deterministic assertions for important behaviors such as tool selection, tool arguments, order lookup, abstention, and protection of sensitive information.

## Setup & Installation

### Prerequisites

Before running the project, make sure the following are installed:

- Python 3.10 or later
- Git
- `pip`

### Clone the Repository

Clone the repository and move into the project directory:

```bash
git clone https://github.com/aayushasawale/ai-agent-intern-test.git
cd ai-agent-intern-test
```

### Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### Run the Tests

Run the complete test suite:

```bash
pytest -q
```

The expected final result is:

```text
33 passed
```

## Configuration & Environment Variables

The current implementation is designed to work with the supplied assignment data and does not require external API credentials for the automated test suite.

### Data Sources

The agent uses the resources provided with the assignment:

- Knowledge-base documents from `knowledge-base/`
- Mock order data from `data/`
- Evaluation scenarios from `evaluation/`

No private credentials or API keys are required to run the automated tests.

### Local Configuration

If additional configuration is required for a specific deployment or model provider, credentials should be supplied through environment variables rather than being hard-coded into the source code.

Sensitive configuration files such as `.env` should not be committed to GitHub.

## Technical Choices

### Application Framework

The application is implemented as a custom Python
support agent rather than using a large agent
framework. This keeps the system small, explicit,
and easy to test.

### Retrieval Approach

The RAG pipeline is implemented as a local semantic
retrieval system over the supplied knowledge-base documents.

#### Embeddings

The project uses the `all-MiniLM-L6-v2` Sentence Transformer
model to convert document chunks and user queries into
embedding vectors.

Embeddings are normalized before being stored and retrieved.

```text
Knowledge Base Documents
          |
          v
     Document Chunks
          |
          v
 Sentence Transformer
 all-MiniLM-L6-v2
          |
          v
   Embedding Vectors
```

### Order Data Storage

Order information is stored in the supplied JSON data and accessed through a dedicated order lookup function.

The complete order dataset is not passed directly to the agent. Only the relevant lookup result is used when order information is required.

### Testing Framework

The project uses `pytest` for automated regression testing and deterministic evaluation assertions.

This allows important behaviors such as tool calls, tool arguments, privacy constraints, order handling, and safe responses to be verified consistently.

## Running the Project

### 1. Create a Virtual Environment

Create and activate a Python virtual environment:

```bash
python -m venv .venv





            
## Demo

A short demonstration of the AI Support Agent covering:

- RAG-based knowledge-base question answering with source citation
- Order lookup for `ORD-1007`
- Multi-turn follow-up without repeating the order ID
- Safe handling of an unknown order (`ORD-9999`)
- Final automated regression test results (`33/33 passed`)

[Watch the Demo Video](https://www.youtube.com/watch?v=Gt1zMvuUgzk)


