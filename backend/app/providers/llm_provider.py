from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import httpx
from loguru import logger

from app.core.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion from messages."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return response.choices[0].message.content
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        return {
            "content": response.choices[0].message.content,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    
    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            return {
                "content": data["message"]["content"],
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            }


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        logger.info(f"MockLLM generate called with prompt length: {len(prompt)}")
        
        # Return contextual mock responses based on prompt content
        prompt_lower = prompt.lower()
        
        if "договор" in prompt_lower or "contract" in prompt_lower:
            return """На основании анализа представленного договора:

**Краткое содержание:**
Документ представляет собой стандартный договор с типичными положениями о правах и обязанностях сторон.

**Ключевые условия:**
1. Предмет договора определен четко
2. Срок действия и условия расторжения соответствуют практике
3. Ответственность сторон распределена сбалансированно

**Рекомендации:**
- Рекомендуется уточнить порядок разрешения споров
- Следует добавить положение о форс-мажоре если отсутствует"""

        elif "риск" in prompt_lower or "risk" in prompt_lower or "анализ" in prompt_lower:
            return """**Анализ рисков документа:**

1. **Высокий риск:** Отсутствие ограничения ответственности
   - Рекомендация: Добавить cap на убытки

2. **Средний риск:** Неопределенность в сроках исполнения
   - Рекомендация: Уточнить конкретные даты

3. **Низкий риск:** Стандартные условия конфиденциальности
   - Комментарий: Соответствует рыночной практике"""

        elif "проверк" in prompt_lower or "due diligence" in prompt_lower:
            return """**Отчет о проверке компании**

**1. Общая информация:**
Компания зарегистрирована и ведет активную деятельность.

**2. Судебные споры:**
Выявлено несколько судебных дел, требующих внимания.

**3. Финансовые риски:**
Финансовое состояние стабильное, задолженности в пределах нормы.

**4. Регуляторные риски:**
Компания соблюдает основные требования законодательства.

**Общая оценка риска: СРЕДНИЙ**"""

        elif "одобрени" in prompt_lower or "корпоративн" in prompt_lower:
            return """**Юридическое заключение по вопросу корпоративного одобрения**

В соответствии с действующим законодательством РФ:

1. **Общие требования:**
   Согласно ст. 46 Федерального закона "Об обществах с ограниченной ответственностью", сделки, связанные с отчуждением долей, могут требовать одобрения общего собрания участников.

2. **Применительно к вашему вопросу:**
   Отчуждение 25% доли в ООО в пользу иностранного инвестора, как правило, требует:
   - Одобрения общего собрания участников (если предусмотрено уставом)
   - Соблюдения преимущественного права покупки других участников
   - Проверки ограничений в уставе на отчуждение третьим лицам

3. **Рекомендации:**
   - Проверить устав общества на наличие ограничений
   - Уведомить других участников о намерении продажи
   - Получить корпоративное одобрение при необходимости

**Источники:** ГК РФ, ФЗ "Об ООО", судебная практика"""

        else:
            return """Спасибо за ваш вопрос. На основании анализа доступной информации:

Для предоставления точного ответа рекомендуется уточнить следующие детали:
1. Конкретная юрисдикция применимого права
2. Характер правоотношений между сторонами
3. Наличие специальных условий или ограничений

При необходимости обратитесь к специалисту для детальной консультации."""

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> Dict[str, Any]:
        # Get last user message
        last_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break
        
        content = await self.generate(last_message, temperature=temperature, max_tokens=max_tokens)
        
        return {
            "content": content,
            "prompt_tokens": sum(len(m.get("content", "")) // 4 for m in messages),
            "completion_tokens": len(content) // 4,
            "total_tokens": sum(len(m.get("content", "")) // 4 for m in messages) + len(content) // 4,
        }


# Provider factory
_llm_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider instance."""
    global _llm_provider
    
    if _llm_provider is None:
        provider_type = settings.llm_provider.lower()
        
        if provider_type == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not set, falling back to mock provider")
                _llm_provider = MockLLMProvider()
            else:
                _llm_provider = OpenAIProvider()
                logger.info("Using OpenAI LLM provider")
        elif provider_type == "ollama":
            _llm_provider = OllamaProvider()
            logger.info(f"Using Ollama LLM provider at {settings.ollama_base_url}")
        else:
            _llm_provider = MockLLMProvider()
            logger.info("Using Mock LLM provider")
    
    return _llm_provider

