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