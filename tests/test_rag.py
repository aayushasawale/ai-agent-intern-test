import json
from pathlib import Path

from app.rag.loader import load_knowledge_base
from app.rag.chunker import chunk_documents
from app.rag.vector_store import VectorStore
from app.rag.retriever import Retriever
from app.rag.ranking import rank_chunks
from app.rag.evidence import analyze_evidence
from app.tools.orders import OrderLookup
from app.tools.order_logic import interpret_order_status
from app.agent.agent import SupportAgent
from app.agent.policy_agent import PolicyAgent
from app.agent.support_agent import SupportAgent


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_BASE = PROJECT_ROOT / "knowledge-base"


def test_load_all_knowledge_documents():
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    assert len(documents) == 14


def test_returns_policy_metadata():
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    returns_policy = next(
        document
        for document in documents
        if document.document_id == "RET-2026-01"
    )

    assert returns_policy.title == "Returns Policy"
    assert returns_policy.metadata["status"] == "active"
    assert returns_policy.metadata["policy_authority"] == "official"
    assert returns_policy.metadata["effective_date"] == "2026-04-01"
    assert returns_policy.metadata["supersedes"] == "RET-2024-01"


def test_documents_have_content():
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    for document in documents:
        assert document.content.strip()
        assert document.source_file.endswith(".md")



def test_chunk_documents():
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    assert len(chunks) > 14

    for chunk in chunks:
        assert chunk.chunk_id
        assert chunk.document_id
        assert chunk.source_file
        assert chunk.heading
        assert chunk.text.strip()


def test_chunk_preserves_metadata():
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    returns_chunks = [
        chunk
        for chunk in chunks
        if chunk.document_id == "RET-2026-01"
    ]

    assert returns_chunks

    for chunk in returns_chunks:
        assert chunk.metadata["status"] == "active"
        assert chunk.metadata["policy_authority"] == "official"


def test_chunk_preserves_heading():
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    return_window_chunks = [
        chunk
        for chunk in chunks
        if (
            chunk.document_id == "RET-2026-01"
            and chunk.heading == "Standard return window"
        )
    ]

    assert return_window_chunks

def test_vector_store_indexes_chunks(tmp_path):
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    store = VectorStore(
        persist_directory=tmp_path / "chroma"
    )

    store.add_chunks(chunks)

    assert store.count() == len(chunks)


def test_vector_store_can_retrieve_return_policy(tmp_path):
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    store = VectorStore(
        persist_directory=tmp_path / "chroma"
    )

    store.add_chunks(chunks)

    results = store.search(
        "How many days do I have to return an item?",
        n_results=5,
    )

    assert results["documents"]
    assert results["metadatas"]

    returned_sources = [
        metadata["source_file"]
        for metadata in results["metadatas"][0]
    ]

    assert "01-returns-policy-current.md" in returned_sources



def build_test_vector_store(tmp_path):
    documents = load_knowledge_base(KNOWLEDGE_BASE)

    chunks = chunk_documents(documents)

    store = VectorStore(
        persist_directory=tmp_path / "chroma"
    )

    store.add_chunks(chunks)

    return store


def test_retriever_returns_chunks(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    results = retriever.retrieve(
        "How many days do I have to return an item?"
    )

    assert results
    assert results[0].text
    assert results[0].source_file
    assert results[0].heading
    assert results[0].document_id


def test_retriever_finds_current_returns_policy(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    results = retriever.retrieve(
        "What is the standard return window?"
    )

    sources = [
        result.source_file
        for result in results
    ]

    assert "01-returns-policy-current.md" in sources


def test_ranking_prefers_active_official_source(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    results = retriever.retrieve(
        "What is the return policy?"
    )

    ranked = rank_chunks(results)

    assert ranked

    top = ranked[0].chunk

    assert top.metadata["status"] == "active"
    assert top.metadata["policy_authority"] == "official"

def test_breeze_tumbler_conflict_is_detected(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    results = retriever.retrieve(
        "Can I put the entire Breeze Tumbler in the dishwasher?",
        n_results=8,
    )

    ranked = rank_chunks(results)

    evidence = analyze_evidence(ranked)

    assert evidence.conflict_detected is True
    assert evidence.requires_handoff is True


def test_breeze_tumbler_conflict_keeps_both_sources(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    results = retriever.retrieve(
        "Can I put the entire Breeze Tumbler in the dishwasher?",
        n_results=8,
    )

    ranked = rank_chunks(results)

    evidence = analyze_evidence(ranked)

    sources = {
        chunk.source_file
        for chunk in evidence.chunks
    }

    assert "11-product-care.md" in sources
    assert "12-breeze-tumbler-product-card.md" in sources




def test_order_lookup_valid_order():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1007")

    assert result["found"] is True
    assert result["order_id"] == "ORD-1007"
    assert result["status"] == "shipped"
    assert result["carrier"] == "UPS"
    assert result["estimated_delivery"] == "2026-08-22"

def test_order_id_normalization():
    lookup = OrderLookup()

    result = lookup.lookup("  ord-1007 ")

    assert result["found"] is True
    assert result["order_id"] == "ORD-1007"



def test_unknown_order():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-9999")

    assert result["found"] is False
    assert "not found" in result["message"].lower()



def test_order_lookup_does_not_expose_sensitive_fields():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1007")

    result_text = json.dumps(result).lower()

    assert "email" not in result_text
    assert "shipping_address" not in result_text
    assert "risk_score" not in result_text
    assert "warehouse_note" not in result_text
    assert "support_tags" not in result_text



def test_cancelled_order_status_is_preserved():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1004")

    assert result["found"] is True
    assert result["status"] == "cancelled"


def test_shipped_order_can_have_missing_eta():
    lookup = OrderLookup()

    result = lookup.lookup("ORD-1011")

    assert result["found"] is True
    assert result["status"] == "shipped"
    assert result["estimated_delivery"] is None





def test_cancelled_order_ignores_stale_eta():
    order = {
        "found": True,
        "order_id": "ORD-1004",
        "status": "cancelled",
        "estimated_delivery": "2026-08-25",
    }

    result = interpret_order_status(order)

    assert result["action"] == "cancelled"
    assert "cancelled" in result["customer_message"].lower()
    assert "2026-08-25" not in result["customer_message"]


def test_shipped_order_with_eta():
    order = {
        "found": True,
        "order_id": "ORD-1007",
        "status": "shipped",
        "estimated_delivery": "2026-08-22",
    }

    result = interpret_order_status(order)

    assert result["action"] == "shipped"
    assert "2026-08-22" in result["customer_message"]


def test_shipped_order_without_eta():
    order = {
        "found": True,
        "order_id": "ORD-1011",
        "status": "shipped",
        "estimated_delivery": None,
    }

    result = interpret_order_status(order)

    assert result["action"] == "shipped_eta_unavailable"
    assert "not currently available" in result["customer_message"]


def test_unknown_order_status():
    order = {
        "found": False,
        "order_id": "ORD-9999",
    }

    result = interpret_order_status(order)

    assert result["action"] == "not_found"


def test_delivered_order():
    order = {
        "found": True,
        "order_id": "ORD-1005",
        "status": "delivered",
        "estimated_delivery": "2026-08-20",
    }

    result = interpret_order_status(order)

    assert result["action"] == "delivered"




def test_agent_asks_for_missing_order_id():
    agent = SupportAgent()

    response = agent.handle_order_question(
        None
    )

    assert response.tool_called is None
    assert "order ID" in response.answer


def test_agent_looks_up_valid_order():
    agent = SupportAgent()

    response = agent.handle_order_question(
        "ORD-1007"
    )

    assert response.tool_called == "order_lookup"
    assert response.tool_arguments == {
        "order_id": "ORD-1007"
    }

    assert "shipped" in response.answer.lower()
    assert "ups" in response.answer.lower()
    assert "2026-08-22" in response.answer


def test_agent_does_not_use_stale_eta_for_cancelled_order():
    agent = SupportAgent()

    response = agent.handle_order_question(
        "ORD-1004"
    )

    assert response.tool_called == "order_lookup"

    assert "cancelled" in response.answer.lower()

    assert "2026-08-16" not in response.answer
    assert "still arriving" not in response.answer.lower()




def test_agent_handles_unknown_order():
    agent = SupportAgent()

    response = agent.handle_order_question(
        "ORD-9999"
    )

    assert response.tool_called == "order_lookup"
    assert "couldn't find" in response.answer.lower()




def test_policy_agent_returns_sources(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    agent = PolicyAgent(
        retriever
    )

    response = agent.answer(
        "What is the standard return window?"
    )

    assert response.handoff is False

    assert len(response.sources) > 0

    # The response must cite the current returns policy.
    assert any(
        "01-returns-policy-current.md" in source
        for source in response.sources
    )

    assert any(
    source.startswith("01-returns-policy-current.md")
    and "—" in source
    and source.split("—", 1)[1].strip()
    for source in response.sources
)
    



def test_policy_agent_handles_breeze_tumbler_conflict(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    agent = PolicyAgent(
        retriever
    )

    response = agent.answer(
        "Can I put the entire Breeze Tumbler in the dishwasher?"
    )

    assert response.conflict_detected is True
    assert response.handoff is True

    assert any(
        "11-product-care.md" in source
        for source in response.sources
    )

    assert any(
        "12-breeze-tumbler-product-card.md" in source
        for source in response.sources
    )


def test_support_agent_routes_order_question(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    agent = SupportAgent(retriever)

    response = agent.answer(
        "Where is my order ORD-1007?"
    )

    assert response["type"] == "order"
    assert response["order_id"] == "ORD-1007"
    assert response["answer"]["found"] is True


def test_support_agent_routes_policy_question(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    agent = SupportAgent(retriever)

    response = agent.answer(
        "What is the standard return window?"
    )

    assert response["type"] == "policy"


def test_support_agent_asks_for_order_id(tmp_path):
    store = build_test_vector_store(tmp_path)

    retriever = Retriever(store)

    agent = SupportAgent(retriever)

    response = agent.answer(
        "Where is my order?"
    )

    assert response["type"] == "clarification"
    assert "order ID" in response["answer"]