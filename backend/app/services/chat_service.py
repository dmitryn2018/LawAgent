from typing import Optional, List
from sqlalchemy.orm import Session
from loguru import logger
from datetime import datetime

from app.core.database import SessionLocal
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatCompletionResponse, ChatMessageResponse, SourceReference
from app.services.search_service import SearchService
from app.providers.llm_provider import get_llm_provider


class ChatService:
    """Service for chat operations."""
    
    SYSTEM_PROMPTS = {
        "question": """Вы - опытный юридический консультант AI-системы юридической фирмы. 
Ваша задача - отвечать на вопросы по праву, используя предоставленный контекст из документов.

Правила:
1. Отвечайте точно и по существу вопроса
2. Ссылайтесь на источники, когда это уместно
3. Если информации недостаточно, честно сообщите об этом
4. Используйте профессиональную юридическую терминологию
5. Структурируйте ответ с выделением ключевых моментов

Контекст из документов:
{context}""",
        
        "case_review": """Вы - юридический аналитик AI-системы юридической фирмы.
Ваша задача - проанализировать и дать обзор юридического дела или ситуации.

Правила:
1. Выделите ключевые факты
2. Определите применимые нормы права
3. Оцените правовые риски
4. Предложите возможные стратегии
5. Ссылайтесь на релевантную практику из контекста

Контекст из документов:
{context}""",
        
        "case_search": """Вы - юридический исследователь AI-системы юридической фирмы.
Ваша задача - найти и проанализировать похожие дела или прецеденты.

Правила:
1. Найдите аналогичные случаи в предоставленном контексте
2. Сравните обстоятельства дел
3. Выделите ключевые различия и сходства
4. Оцените применимость прецедентов
5. Предоставьте краткое резюме каждого найденного дела

Контекст из документов:
{context}"""
    }
    
    @staticmethod
    async def generate_response(
        session_id: int,
        message: str,
        jurisdiction: Optional[str],
        mode: str,
        db: Session
    ) -> ChatCompletionResponse:
        """Generate AI response for a chat message."""
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=message
        )
        db.add(user_message)
        db.commit()
        
        # Search for relevant documents
        search_results = await SearchService.search(
            query=message,
            jurisdiction=jurisdiction,
            top_k=7,
            db=db
        )
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for i, result in enumerate(search_results):
            context_parts.append(f"[Источник {i+1}: {result.document_title}]\n{result.text}")
            sources.append(SourceReference(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                title=result.document_title,
                snippet=result.text[:200] + "..." if len(result.text) > 200 else result.text,
                relevance=result.relevance
            ))
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "Релевантные документы не найдены."
        
        # Get system prompt for mode
        system_prompt = ChatService.SYSTEM_PROMPTS.get(mode, ChatService.SYSTEM_PROMPTS["question"])
        system_prompt = system_prompt.format(context=context)
        
        # Build conversation history
        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent history (last 10 messages)
        for msg in history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Generate response
        llm_provider = get_llm_provider()
        response = await llm_provider.generate_chat(
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response["content"],
            sources=[s.model_dump() for s in sources],
            prompt_tokens=response.get("prompt_tokens"),
            completion_tokens=response.get("completion_tokens")
        )
        db.add(assistant_message)
        
        # Update session title if first message
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session and not session.title:
            session.title = message[:50] + "..." if len(message) > 50 else message
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(assistant_message)
        
        return ChatCompletionResponse(
            message=ChatMessageResponse.model_validate(assistant_message),
            sources=sources
        )

