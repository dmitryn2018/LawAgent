import os
import uuid
from typing import Optional, List, Dict, Any
from loguru import logger

from app.core.config import settings
from app.models.template import Template
from app.schemas.template import TemplateRenderResponse
from app.providers.llm_provider import get_llm_provider


class TemplateService:
    """Service for template rendering operations."""
    
    @staticmethod
    async def render_template(
        template: Template,
        form_data: Dict[str, Any],
        include_sections: Optional[List[str]] = None,
        use_ai: bool = False
    ) -> TemplateRenderResponse:
        """Render a template with form data."""
        try:
            from docxtpl import DocxTemplate
            
            # Load template
            if not os.path.exists(template.file_path):
                # If template file doesn't exist, generate from form data
                return await TemplateService._generate_from_form(
                    template, form_data, include_sections, use_ai
                )
            
            doc = DocxTemplate(template.file_path)
            
            # Prepare context with form data
            context = dict(form_data)
            
            # Handle optional sections
            if template.optional_sections:
                for section in template.optional_sections:
                    context[f"include_{section}"] = section in (include_sections or [])
            
            # Use AI to generate descriptive parts if requested
            if use_ai:
                context = await TemplateService._enhance_with_ai(context, template)
            
            # Render template
            doc.render(context)
            
            # Save rendered document
            file_id = str(uuid.uuid4())
            output_dir = os.path.join(settings.storage_path, "rendered")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{file_id}.docx")
            doc.save(output_path)
            
            # Extract text for preview
            from docx import Document
            rendered_doc = Document(output_path)
            rendered_text = "\n\n".join([p.text for p in rendered_doc.paragraphs if p.text.strip()])
            
            return TemplateRenderResponse(
                rendered_text=rendered_text,
                file_id=file_id,
                download_url=f"/api/templates/{template.id}/download/{file_id}"
            )
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            # Fallback to simple text generation
            return await TemplateService._generate_from_form(
                template, form_data, include_sections, use_ai
            )
    
    @staticmethod
    async def _generate_from_form(
        template: Template,
        form_data: Dict[str, Any],
        include_sections: Optional[List[str]],
        use_ai: bool
    ) -> TemplateRenderResponse:
        """Generate document text from form data without template file."""
        
        if use_ai:
            return await TemplateService._generate_with_ai(template, form_data, include_sections)
        
        # Simple text generation based on template category
        category = template.category or "general"
        
        generators = {
            "nda": TemplateService._generate_nda,
            "spa": TemplateService._generate_spa,
            "employment": TemplateService._generate_employment,
        }
        
        generator = generators.get(category, TemplateService._generate_generic)
        rendered_text = generator(form_data, include_sections)
        
        return TemplateRenderResponse(
            rendered_text=rendered_text,
            file_id=None,
            download_url=None
        )
    
    @staticmethod
    async def _generate_with_ai(
        template: Template,
        form_data: Dict[str, Any],
        include_sections: Optional[List[str]]
    ) -> TemplateRenderResponse:
        """Generate document using AI."""
        llm_provider = get_llm_provider()
        
        prompt = f"""Сгенерируй юридический документ типа "{template.name}" на основе следующих данных:

Данные формы:
{chr(10).join(f'- {k}: {v}' for k, v in form_data.items())}

Включить секции: {', '.join(include_sections) if include_sections else 'все стандартные'}

Требования:
1. Документ должен быть юридически корректным
2. Использовать профессиональную юридическую терминологию
3. Включить все необходимые реквизиты
4. Структурировать документ с нумерацией разделов

Сгенерируй полный текст документа:"""
        
        response = await llm_provider.generate(
            prompt=prompt,
            system_prompt="Вы - профессиональный юрист, специализирующийся на составлении договоров.",
            temperature=0.5,
            max_tokens=3000
        )
        
        return TemplateRenderResponse(
            rendered_text=response,
            file_id=None,
            download_url=None
        )
    
    @staticmethod
    async def _enhance_with_ai(context: Dict[str, Any], template: Template) -> Dict[str, Any]:
        """Enhance form data with AI-generated content."""
        llm_provider = get_llm_provider()
        
        # Generate purpose/description if not provided
        if not context.get("purpose") and context.get("subject"):
            prompt = f"Опиши кратко (2-3 предложения) цель и предмет соглашения: {context.get('subject')}"
            response = await llm_provider.generate(prompt, max_tokens=200)
            context["purpose"] = response
        
        return context
    
    @staticmethod
    def _generate_nda(form_data: Dict[str, Any], include_sections: Optional[List[str]]) -> str:
        """Generate NDA document text."""
        party1 = form_data.get("party1", "[СТОРОНА 1]")
        party2 = form_data.get("party2", "[СТОРОНА 2]")
        subject = form_data.get("subject", "[ПРЕДМЕТ]")
        term = form_data.get("term", "3 (три) года")
        governing_law = form_data.get("governing_law", "Российской Федерации")
        
        text = f"""СОГЛАШЕНИЕ О КОНФИДЕНЦИАЛЬНОСТИ
(Non-Disclosure Agreement)

г. Москва                                                    «___» __________ 20__ г.

{party1}, далее именуемое «Раскрывающая сторона», с одной стороны, и {party2}, далее именуемое «Получающая сторона», с другой стороны, совместно именуемые «Стороны», заключили настоящее Соглашение о нижеследующем:

1. ПРЕДМЕТ СОГЛАШЕНИЯ

1.1. Раскрывающая сторона обязуется передать Получающей стороне конфиденциальную информацию, а Получающая сторона обязуется обеспечить её надлежащую защиту.

1.2. Предмет раскрытия информации: {subject}.

2. ОПРЕДЕЛЕНИЕ КОНФИДЕНЦИАЛЬНОЙ ИНФОРМАЦИИ

2.1. Под конфиденциальной информацией в рамках настоящего Соглашения понимается любая информация, переданная одной Стороной другой Стороне в письменной, устной или иной форме, включая, но не ограничиваясь:
   - техническая документация;
   - коммерческая информация;
   - финансовые данные;
   - персональные данные;
   - ноу-хау и иные сведения.

3. ОБЯЗАТЕЛЬСТВА СТОРОН

3.1. Получающая сторона обязуется:
   - не разглашать конфиденциальную информацию третьим лицам;
   - использовать информацию исключительно в целях, предусмотренных настоящим Соглашением;
   - обеспечить защиту информации от несанкционированного доступа.

4. СРОК ДЕЙСТВИЯ

4.1. Настоящее Соглашение вступает в силу с момента подписания и действует в течение {term}.

4.2. Обязательства по сохранению конфиденциальности сохраняют силу в течение 5 (пяти) лет после прекращения действия Соглашения.

5. ОТВЕТСТВЕННОСТЬ

5.1. За нарушение условий настоящего Соглашения виновная Сторона несёт ответственность в соответствии с действующим законодательством {governing_law}.

6. ПРИМЕНИМОЕ ПРАВО

6.1. Настоящее Соглашение регулируется законодательством {governing_law}.

7. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН

Раскрывающая сторона:                    Получающая сторона:
{party1}                                  {party2}

_____________________                     _____________________
        (подпись)                                (подпись)
"""
        return text
    
    @staticmethod
    def _generate_spa(form_data: Dict[str, Any], include_sections: Optional[List[str]]) -> str:
        """Generate simplified Share Purchase Agreement."""
        seller = form_data.get("seller", "[ПРОДАВЕЦ]")
        buyer = form_data.get("buyer", "[ПОКУПАТЕЛЬ]")
        company = form_data.get("company", "[КОМПАНИЯ]")
        shares = form_data.get("shares", "100%")
        price = form_data.get("price", "[ЦЕНА]")
        
        text = f"""ДОГОВОР КУПЛИ-ПРОДАЖИ АКЦИЙ (ДОЛЕЙ)
(Share Purchase Agreement - Упрощённая форма)

г. Москва                                                    «___» __________ 20__ г.

{seller}, далее именуемый «Продавец», с одной стороны, и {buyer}, далее именуемый «Покупатель», с другой стороны, заключили настоящий Договор о нижеследующем:

1. ПРЕДМЕТ ДОГОВОРА

1.1. Продавец обязуется передать в собственность Покупателя, а Покупатель обязуется принять и оплатить {shares} акций (долей) в уставном капитале {company} (далее - «Акции»).

2. ЦЕНА И ПОРЯДОК ОПЛАТЫ

2.1. Цена Акций составляет: {price}.
2.2. Оплата производится в следующем порядке: [указать порядок].

3. ЗАВЕРЕНИЯ И ГАРАНТИИ ПРОДАВЦА

3.1. Продавец заверяет и гарантирует, что:
   - является законным владельцем Акций;
   - Акции свободны от обременений;
   - получены все необходимые корпоративные одобрения.

4. ПЕРЕХОД ПРАВА СОБСТВЕННОСТИ

4.1. Право собственности на Акции переходит к Покупателю с момента [указать момент].

5. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ

5.1. Настоящий Договор вступает в силу с момента подписания.

ПОДПИСИ СТОРОН:

Продавец:                                 Покупатель:
{seller}                                  {buyer}

_____________________                     _____________________
"""
        return text
    
    @staticmethod
    def _generate_employment(form_data: Dict[str, Any], include_sections: Optional[List[str]]) -> str:
        """Generate simplified Employment Contract."""
        employer = form_data.get("employer", "[РАБОТОДАТЕЛЬ]")
        employee = form_data.get("employee", "[РАБОТНИК]")
        position = form_data.get("position", "[ДОЛЖНОСТЬ]")
        salary = form_data.get("salary", "[ОКЛАД]")
        
        text = f"""ТРУДОВОЙ ДОГОВОР
(Упрощённая форма)

г. Москва                                                    «___» __________ 20__ г.

{employer}, далее именуемый «Работодатель», с одной стороны, и {employee}, далее именуемый «Работник», с другой стороны, заключили настоящий Договор о нижеследующем:

1. ПРЕДМЕТ ДОГОВОРА

1.1. Работодатель обязуется предоставить Работнику работу по должности: {position}.
1.2. Работник обязуется лично выполнять указанную работу.

2. СРОК ДОГОВОРА

2.1. Настоящий Договор заключён на неопределённый срок.
2.2. Дата начала работы: [указать дату].

3. УСЛОВИЯ ОПЛАТЫ ТРУДА

3.1. Должностной оклад Работника составляет: {salary} рублей в месяц.
3.2. Заработная плата выплачивается два раза в месяц.

4. РЕЖИМ РАБОТЫ И ОТДЫХА

4.1. Работнику устанавливается 40-часовая рабочая неделя.
4.2. Ежегодный оплачиваемый отпуск - 28 календарных дней.

5. ПРАВА И ОБЯЗАННОСТИ СТОРОН

5.1. Работник обязан добросовестно исполнять трудовые обязанности.
5.2. Работодатель обязан обеспечить условия труда согласно законодательству.

ПОДПИСИ СТОРОН:

Работодатель:                             Работник:
{employer}                                {employee}

_____________________                     _____________________
"""
        return text
    
    @staticmethod
    def _generate_generic(form_data: Dict[str, Any], include_sections: Optional[List[str]]) -> str:
        """Generate generic document from form data."""
        lines = ["ДОКУМЕНТ", "", f"Дата: «___» __________ 20__ г.", ""]
        
        for key, value in form_data.items():
            lines.append(f"{key.replace('_', ' ').title()}: {value}")
        
        lines.extend(["", "ПОДПИСИ СТОРОН:", "", "_____________________"])
        
        return "\n".join(lines)

