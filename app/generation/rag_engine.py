import logging
from typing import List, Dict, Any, Optional

from app.generation.prompt_builder import SYSTEM_PROMPT, build_rag_prompt
from app.generation.citation_tracker import extract_citations
from app.generation.conversation import ConversationManager

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(
        self,
        retriever,
        ollama_client,
        conversation_manager: Optional[ConversationManager] = None
    ):
        self.retriever = retriever
        self.ollama_client = ollama_client
        self.conversation_manager = conversation_manager or ConversationManager()

    def answer_question(
        self,
        question: str,
        document_id: Optional[str] = None,
        retrieval_mode: str = "hybrid",
        top_k: int = 5,
        session_id: Optional[str] = None,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Execute full RAG generation flow:
        1. Retrieve relevant passages (Hybrid / Dense / Lexical)
        2. Handle zero-result or insufficient context cases gracefully
        3. Build anti-injection grounded prompt
        4. Query local Ollama LLM
        5. Extract structured citations and evidence
        6. Update multi-turn conversation memory
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        q_clean = question.strip()

        # 1. Retrieve evidence
        retrieved_chunks = self.retriever.retrieve(
            query=q_clean,
            limit=top_k,
            document_id=document_id,
            mode=retrieval_mode
        )

        citations = extract_citations(retrieved_chunks)

        # 2. Insufficient evidence fallback if no chunks retrieved
        if not retrieved_chunks:
            answer = "I do not have sufficient information in the provided documents to answer this question. Please upload relevant documents first or rephrase your question."
            if session_id:
                self.conversation_manager.add_turn(session_id, q_clean, answer, [])
            return {
                "answer": answer,
                "citations": [],
                "retrieved_evidence": [],
                "session_id": session_id,
                "model": getattr(self.ollama_client, "default_model", "none"),
                "retrieval_mode": retrieval_mode
            }

        # 3. Conversation history
        history = self.conversation_manager.get_history(session_id) if session_id else []

        # 4. Construct prompt
        prompt = build_rag_prompt(
            query=q_clean,
            retrieved_chunks=retrieved_chunks,
            conversation_history=history
        )

        # 5. Query Ollama
        try:
            answer = self.ollama_client.generate(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                temperature=temperature
            )
        except Exception as exc:
            logger.error("LLM generation error: %s", exc)
            raise

        # 6. Record turn
        if session_id:
            self.conversation_manager.add_turn(session_id, q_clean, answer, citations)

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_evidence": citations,
            "session_id": session_id,
            "model": getattr(self.ollama_client, "default_model", "ollama"),
            "retrieval_mode": retrieval_mode
        }
