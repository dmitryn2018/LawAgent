from typing import Optional, List
from sqlalchemy.orm import Session
from loguru import logger
import re
import uuid
import os

from app.models.clause import Clause
from app.schemas.analysis import (
    DocumentAnalysisResponse, DocumentRisk, TextSpan, DealImpact,
    ClauseSuggestionResponse, SuggestedClause
)
from app.providers.llm_provider import get_llm_provider
from app.core.config import settings


class AnalysisService:
    """Service for document analysis operations."""
    
    @staticmethod
    async def analyze_document(
        text: str,
        document_type: Optional[str],
        jurisdiction: Optional[str],
        db: Session
    ) -> DocumentAnalysisResponse:
        """Analyze document and return summary, risks, and recommendations."""
        llm_provider = get_llm_provider()
        
        # Load analysis prompt
        prompt_path = os.path.join(settings.storage_path, "..", "prompts", "document_analysis.txt")
        system_prompt = "Вы - опытный юрист-аналитик. Проводите тщательный анализ документов и выявляете потенциальные риски."
        
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        
        # Create analysis prompt
        doc_type_str = f"типа '{document_type}'" if document_type else ""
        jurisdiction_str = f"(юрисдикция: {jurisdiction})" if jurisdiction else ""
        
        prompt = f"""Проанализируй следующий юридический документ {doc_type_str} {jurisdiction_str}:

---
{text[:8000]}
---

Предоставь анализ СТРОГО в следующем формате (соблюдай порядок секций):

## КРАТКОЕ СОДЕРЖАНИЕ
(2-3 абзаца описания документа)

## ОБЩИЙ УРОВЕНЬ РИСКА
(одно слово: низкий / средний / высокий)

## СТОРОНЫ ДОГОВОРА
- (название первой стороны и её роль)
- (название второй стороны и её роль)

## ВЫЯВЛЕННЫЕ РИСКИ
Для каждого риска используй ТОЧНО такой формат:

### Риск 1
- Название: (краткое название риска)
- Уровень: (низкий/средний/высокий)
- Влияние на сделку: (deal-breaker / торгуемо / косметика)  
- Описание: (подробное описание риска и его последствий)
- Цитата: "(цитата из документа, если есть)"

### Риск 2
(аналогично)

## ВЛИЯНИЕ НА СДЕЛКУ
- Цена: (как влияет на оценку/цену)
- Структура: (как влияет на структуру сделки)
- Контроль: (как влияет на управление)

## РЕКОМЕНДАЦИИ
- (конкретное действие 1)
- (конкретное действие 2)

## КЛЮЧЕВЫЕ УСЛОВИЯ
- (условие 1)
- (условие 2)
"""
        
        response = await llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
            max_tokens=2500
        )
        
        # Parse the response
        summary, risks, recommendations, key_terms, parties, overall_risk_level, deal_impact = (
            AnalysisService._parse_analysis(response, text)
        )
        
        return DocumentAnalysisResponse(
            summary=summary,
            risks=risks,
            recommendations=recommendations,
            key_terms=key_terms,
            parties=parties,
            overall_risk_level=overall_risk_level,
            deal_impact=deal_impact
        )
    
    @staticmethod
    def _parse_analysis(response: str, original_text: str) -> tuple:
        """Parse LLM response into structured data."""
        summary = ""
        risks = []
        recommendations = []
        key_terms = []
        parties = []
        overall_risk_level = "medium"
        deal_impact = None
        
        # Helper to extract section content between headers
        def extract_section(pattern: str, end_patterns: list) -> str:
            end_regex = '|'.join(end_patterns) if end_patterns else '$'
            match = re.search(f'{pattern}(.*?)(?={end_regex}|$)', response, re.DOTALL | re.IGNORECASE)
            if not match:
                return ""
            content = match.group(1).strip()
            # Remove any ## headers that might be inline
            content = re.sub(r'##\s*[А-ЯA-Z][А-ЯA-Zа-яa-z\s]+(?=\n|$)', '', content)
            return content.strip()
        
        # Extract summary
        summary = extract_section(
            r'(?:##\s*)?КРАТКОЕ СОДЕРЖАНИЕ[:\s]*',
            [r'##\s*', r'\d+\.\s+[А-ЯA-Z]']
        )
        if not summary:
            paragraphs = response.split('\n\n')
            summary = paragraphs[0] if paragraphs else response[:500]
        
        # Extract overall risk level
        risk_section = extract_section(r'(?:##\s*)?ОБЩИЙ УРОВЕНЬ РИСКА[:\s]*', [r'##\s*', r'\d+\.\s+[А-ЯA-Z]'])
        risk_level_match = re.search(r'(низкий|средний|высокий|low|medium|high)', risk_section, re.IGNORECASE)
        if risk_level_match:
            level = risk_level_match.group(1).lower()
            if level in ["низкий", "low"]:
                overall_risk_level = "low"
            elif level in ["высокий", "high"]:
                overall_risk_level = "high"
            else:
                overall_risk_level = "medium"
        
        # Extract risks section
        risk_section_text = extract_section(
            r'(?:##\s*)?ВЫЯВЛЕННЫЕ РИСКИ[:\s]*',
            [r'##\s*ВЛИЯНИЕ', r'##\s*РЕКОМЕНДАЦИИ', r'\d+\.\s+ВЛИЯНИЕ', r'\d+\.\s+РЕКОМЕНДАЦИИ']
        )
        
        if risk_section_text:
            # Split by ### headers or numbered risks
            risk_blocks = re.split(r'###\s*[Рр]иск\s*\d+|(?:^|\n)(?=[-•]\s*[Нн]азвание:)', risk_section_text)
            
            for block in risk_blocks[:10]:  # Limit to 10 risks
                block = block.strip()
                if len(block) < 20:
                    continue
                
                # Parse structured risk fields
                title = ""
                description = ""
                severity = "medium"
                impact_on_deal = "negotiable"
                recommendation = None
                
                # Extract title (Название)
                title_match = re.search(r'[-•]?\s*[Нн]азвание[:\s]+(.+?)(?=\n[-•]|\n\s*$|\Z)', block, re.DOTALL)
                if title_match:
                    title = title_match.group(1).strip().strip('*-•').strip()
                
                # Extract severity (Уровень)
                level_match = re.search(r'[-•]?\s*[Уу]ровень[:\s]+(низкий|средний|высокий)', block, re.IGNORECASE)
                if level_match:
                    level = level_match.group(1).lower()
                    severity = "low" if level == "низкий" else ("high" if level == "высокий" else "medium")
                
                # Extract impact on deal
                impact_match = re.search(r'[-•]?\s*[Вв]лияние\s+на\s+сделку[:\s]+(.+?)(?=\n[-•]|\Z)', block)
                if impact_match:
                    impact_text = impact_match.group(1).lower()
                    if "deal-breaker" in impact_text or "критическ" in impact_text:
                        impact_on_deal = "deal_breaker"
                    elif "косметик" in impact_text:
                        impact_on_deal = "cosmetic"
                    else:
                        impact_on_deal = "negotiable"
                
                # Extract description (Описание)
                desc_match = re.search(r'[-•]?\s*[Оо]писание[:\s]+(.+?)(?=\n[-•]\s*[А-Яа-я]|\n[-•]\s*$|\Z)', block, re.DOTALL)
                if desc_match:
                    description = desc_match.group(1).strip().strip('*')
                
                # Extract quote (Цитата)
                quote_match = re.search(r'[-•]?\s*[Цц]итата[:\s]+[«"]?(.+?)[»"]?(?=\n[-•]|\Z)', block, re.DOTALL)
                quote = quote_match.group(1).strip() if quote_match else None
                
                # Fallback: if title not found, use first meaningful line
                if not title:
                    lines = [l.strip() for l in block.split('\n') if l.strip() and not l.strip().startswith('-')]
                    if lines:
                        title = re.sub(r'\*\*([^*]+)\*\*', r'\1', lines[0])[:100]
                
                # Fallback: if description not found, use block without field markers
                if not description:
                    clean_block = re.sub(r'[-•]\s*(Название|Уровень|Влияние|Цитата)[:\s]+[^\n]+\n?', '', block, flags=re.IGNORECASE)
                    description = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_block).strip()
                
                if not title or len(title) < 3:
                    continue
                
                # Add quote to description if present
                if quote and quote not in description:
                    description = f"{description}\n\nЦитата: «{quote}»"
                
                spans = AnalysisService._find_text_spans(block, original_text)
                
                risks.append(DocumentRisk(
                    id=str(uuid.uuid4())[:8],
                    title=title,
                    description=description if description else title,
                    severity=severity,
                    spans=spans,
                    recommendation=recommendation,
                    impact_on_deal=impact_on_deal
                ))
        
        # If no risks parsed, create default ones based on common patterns
        if not risks:
            risks = AnalysisService._detect_common_risks(original_text)
        else:
            # Recalculate overall risk if not explicitly provided
            if not risk_level_match:
                overall_risk_level = AnalysisService._calculate_overall_risk(risks)
        
        # Extract deal impact
        deal_text = extract_section(
            r'(?:##\s*)?ВЛИЯНИЕ НА СДЕЛКУ[:\s]*',
            [r'##\s*РЕКОМЕНДАЦИИ', r'##\s*КЛЮЧЕВЫЕ', r'\d+\.\s+РЕКОМЕНДАЦИИ']
        )
        if deal_text:
            price_match = re.search(r'[-•]?\s*[Цц]ена[:\s]*(.+?)(?=\n[-•]|\Z)', deal_text, re.DOTALL)
            structure_match = re.search(r'[-•]?\s*[Сс]труктур[а]?[:\s]*(.+?)(?=\n[-•]|\Z)', deal_text, re.DOTALL)
            control_match = re.search(r'[-•]?\s*[Кк]онтрол[ья]?[:\s]*(.+?)(?=\n[-•]|\Z)', deal_text, re.DOTALL)
            
            deal_impact = DealImpact(
                price=price_match.group(1).strip() if price_match else "Не определено",
                structure=structure_match.group(1).strip() if structure_match else "Не определено",
                control=control_match.group(1).strip() if control_match else "Не определено"
            )
        
        # Helper to clean list items
        def clean_list_item(text: str) -> str:
            cleaned = text.strip()
            # Remove markdown formatting
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
            # Remove leading dashes/bullets
            cleaned = re.sub(r'^[-•]\s*', '', cleaned).strip()
            return cleaned
        
        def is_valid_item(text: str) -> bool:
            """Check if text is a valid list item (not a section header)."""
            if len(text) < 5:
                return False
            # Skip ## headers and section names
            if re.match(r'^(##|#|\d+\.\s*[А-ЯA-Z]{2,})', text):
                return False
            if re.match(r'^(РЕКОМЕНДАЦИИ|КЛЮЧЕВЫЕ|ВЛИЯНИЕ|ВЫЯВЛЕННЫЕ|ОБЩИЙ|СТОРОНЫ|КРАТКОЕ)', text, re.IGNORECASE):
                return False
            return True
        
        # Extract recommendations
        rec_text = extract_section(
            r'(?:##\s*)?РЕКОМЕНДАЦИИ[:\s]*(?:ПО ДОРАБОТКЕ)?[:\s]*',
            [r'##\s*КЛЮЧЕВЫЕ', r'##\s*СТОРОНЫ', r'\d+\.\s+КЛЮЧЕВЫЕ']
        )
        if rec_text:
            rec_items = re.split(r'\n\s*[-•]\s+|\n\s*\d+[.)]\s+', rec_text)
            recommendations = [clean_list_item(r) for r in rec_items if is_valid_item(clean_list_item(r)) and len(clean_list_item(r)) > 10][:10]
        
        # Extract key terms
        terms_text = extract_section(
            r'(?:##\s*)?КЛЮЧЕВЫЕ УСЛОВИЯ[:\s]*',
            [r'##\s*СТОРОНЫ', r'##\s*РЕКОМЕНДАЦИИ', r'\d+\.\s+СТОРОНЫ']
        )
        if terms_text:
            term_items = re.split(r'\n\s*[-•]\s+|\n\s*\d+[.)]\s+', terms_text)
            key_terms = [clean_list_item(t) for t in term_items if is_valid_item(clean_list_item(t)) and len(clean_list_item(t)) > 5][:10]
        
        # Extract parties (now before recommendations in the prompt)
        parties_text = extract_section(
            r'(?:##\s*)?СТОРОНЫ[:\s]*(?:ДОГОВОРА)?[:\s]*',
            [r'##\s*ВЫЯВЛЕННЫЕ', r'##\s*РИСКИ', r'##\s*ВЛИЯНИЕ', r'##\s*РЕКОМЕНДАЦИИ', r'##\s*КЛЮЧЕВЫЕ', r'\d+\.\s+ВЫЯВЛЕННЫЕ']
        )
        if parties_text:
            party_items = re.split(r'\n\s*[-•]\s+|\n\s*\d+[.)]\s+', parties_text)
            parties = [clean_list_item(p) for p in party_items if is_valid_item(clean_list_item(p))][:5]
        
        return summary, risks, recommendations, key_terms, parties, overall_risk_level, deal_impact
    
    @staticmethod
    def _calculate_overall_risk(risks: List[DocumentRisk]) -> str:
        """Calculate overall risk level from list of risks."""
        if not risks:
            return "low"
        
        # Count severities
        high_count = sum(1 for r in risks if r.severity == "high")
        medium_count = sum(1 for r in risks if r.severity == "medium")
        
        # Count deal breakers
        deal_breaker_count = sum(1 for r in risks if r.impact_on_deal == "deal_breaker")
        
        if deal_breaker_count > 0 or high_count >= 2:
            return "high"
        elif high_count > 0 or medium_count >= 3:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _find_text_spans(risk_description: str, original_text: str) -> List[TextSpan]:
        """Find text spans in original document matching risk description."""
        spans = []
        
        # Look for quoted text in risk description
        quotes = re.findall(r'[«"]([^»"]+)[»"]', risk_description)
        
        for quote in quotes:
            if len(quote) > 10:
                idx = original_text.find(quote)
                if idx >= 0:
                    spans.append(TextSpan(start_char=idx, end_char=idx + len(quote)))
        
        return spans[:3]  # Limit to 3 spans per risk
    
    @staticmethod
    def _detect_common_risks(text: str) -> List[DocumentRisk]:
        """Detect common risks based on text patterns."""
        risks = []
        text_lower = text.lower()
        
        risk_patterns = [
            {
                "pattern": r"неограниченн\w*\s+ответственност",
                "title": "Неограниченная ответственность",
                "description": "В документе отсутствует ограничение ответственности сторон",
                "severity": "high",
                "impact_on_deal": "deal_breaker"
            },
            {
                "pattern": r"штраф\w*\s+в\s+размере\s+[\d\s]+%",
                "title": "Значительные штрафные санкции",
                "description": "Документ содержит положения о штрафных санкциях",
                "severity": "medium",
                "impact_on_deal": "negotiable"
            },
            {
                "pattern": r"отказ\w*\s+от\s+прав",
                "title": "Отказ от прав",
                "description": "Документ содержит положения об отказе от прав",
                "severity": "medium",
                "impact_on_deal": "negotiable"
            },
            {
                "pattern": r"исключительн\w+\s+юрисдикци",
                "title": "Исключительная юрисдикция",
                "description": "Установлена исключительная юрисдикция для разрешения споров",
                "severity": "low",
                "impact_on_deal": "cosmetic"
            },
            {
                "pattern": r"без\s+права\s+расторжени",
                "title": "Ограничение права расторжения",
                "description": "Ограничены возможности одностороннего расторжения договора",
                "severity": "medium",
                "impact_on_deal": "negotiable"
            }
        ]
        
        for pattern_info in risk_patterns:
            match = re.search(pattern_info["pattern"], text_lower)
            if match:
                start_idx = max(0, match.start() - 50)
                end_idx = min(len(text), match.end() + 50)
                
                risks.append(DocumentRisk(
                    id=str(uuid.uuid4())[:8],
                    title=pattern_info["title"],
                    description=pattern_info["description"],
                    severity=pattern_info["severity"],
                    spans=[TextSpan(start_char=match.start(), end_char=match.end())],
                    recommendation=None,
                    impact_on_deal=pattern_info["impact_on_deal"]
                ))
        
        return risks
    
    @staticmethod
    async def generate_client_letter(
        summary: str,
        risks: List[dict],
        deal_impact: Optional[dict],
        language: str = "ru"
    ) -> str:
        """Generate a client letter based on analysis results."""
        llm_provider = get_llm_provider()
        
        # Load client letter prompt
        prompt_path = os.path.join(settings.storage_path, "..", "prompts", "client_letter.txt")
        system_prompt = """Вы - старший партнёр юридической фирмы. 
Ваша задача - составить краткое деловое письмо клиенту по результатам анализа документа.
Письмо должно быть профессиональным, структурированным и кратким (8-12 предложений)."""
        
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        
        # Format risks for prompt
        risk_summary = ""
        top_risks = [r for r in risks if r.get("severity") == "high" or r.get("impact_on_deal") == "deal_breaker"][:3]
        if not top_risks:
            top_risks = risks[:3]
        
        for i, risk in enumerate(top_risks, 1):
            risk_summary += f"{i}. {risk.get('title', 'Риск')}: {risk.get('description', '')}\\n"
        
        # Format deal impact
        deal_summary = ""
        if deal_impact:
            deal_summary = f"""
Влияние на сделку:
- Цена: {deal_impact.get('price', 'Не определено')}
- Структура: {deal_impact.get('structure', 'Не определено')}
- Контроль: {deal_impact.get('control', 'Не определено')}
"""
        
        lang_instruction = "Напишите письмо на русском языке." if language == "ru" else "Write the letter in English."
        
        prompt = f"""На основании проведённого анализа документа составьте краткое деловое письмо клиенту.

РЕЗЮМЕ АНАЛИЗА:
{summary}

ОСНОВНЫЕ РИСКИ:
{risk_summary}
{deal_summary}

{lang_instruction}

Письмо должно:
1. Начинаться с приветствия
2. Кратко изложить результаты анализа
3. Выделить ключевые риски и их значимость для сделки
4. Дать краткие рекомендации по дальнейшим действиям
5. Завершиться предложением обсудить детали

Формат: деловое письмо, 8-12 предложений.
"""
        
        letter_text = await llm_provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.6,
            max_tokens=1000
        )
        
        return letter_text
    
    @staticmethod
    async def suggest_clauses(
        context: str,
        category: Optional[str],
        jurisdiction: Optional[str],
        practice_area: Optional[str],
        db: Session
    ) -> ClauseSuggestionResponse:
        """Suggest relevant clauses based on context."""
        query = db.query(Clause).filter(Clause.is_active == True)
        
        if category:
            query = query.filter(Clause.category == category)
        if jurisdiction:
            query = query.filter(
                (Clause.jurisdiction == jurisdiction) | (Clause.jurisdiction.is_(None))
            )
        if practice_area:
            query = query.filter(
                (Clause.practice_area == practice_area) | (Clause.practice_area.is_(None))
            )
        
        clauses = query.limit(20).all()
        
        # Score clauses by relevance to context
        suggestions = []
        context_lower = context.lower()
        
        for clause in clauses:
            # Simple keyword-based relevance scoring
            relevance = 0.5  # Base relevance
            
            clause_text = (clause.title + " " + clause.body).lower()
            
            # Check for keyword matches
            context_words = set(context_lower.split())
            clause_words = set(clause_text.split())
            common_words = context_words & clause_words
            
            # Exclude common words
            stop_words = {"и", "в", "на", "с", "по", "для", "или", "к", "от", "из", "что", "как"}
            meaningful_common = common_words - stop_words
            
            if meaningful_common:
                relevance += min(0.4, len(meaningful_common) * 0.05)
            
            suggestions.append(SuggestedClause(
                id=clause.id,
                title=clause.title,
                body=clause.body,
                category=clause.category,
                relevance=relevance
            ))
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x.relevance, reverse=True)
        
        return ClauseSuggestionResponse(suggestions=suggestions[:10])
