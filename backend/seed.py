#!/usr/bin/env python3
"""
Seed script for Legal AI System.
Creates demo users, documents, templates, clauses, and indexes documents.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.document import Document
from app.models.template import Template
from app.models.clause import Clause
from app.services.indexing_service import IndexingService

# Seed data path
SEED_DATA_PATH = os.path.join(os.path.dirname(__file__), "seed-data")


def create_users(db: Session):
    """Create demo users."""
    print("Creating users...")
    
    users_data = [
        {
            "email": "admin@example.com",
            "password": "password123",
            "full_name": "Администратор Системы",
            "role": "admin"
        },
        {
            "email": "lawyer@example.com",
            "password": "password123",
            "full_name": "Иван Петров",
            "role": "lawyer"
        },
        {
            "email": "lawyer2@example.com",
            "password": "password123",
            "full_name": "Мария Сидорова",
            "role": "lawyer"
        }
    ]
    
    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                email=user_data["email"],
                password_hash=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"]
            )
            db.add(user)
            print(f"  Created user: {user_data['email']}")
        else:
            print(f"  User already exists: {user_data['email']}")
    
    db.commit()


def create_documents(db: Session):
    """Create demo documents from seed data files."""
    print("Creating documents...")
    
    documents_dir = os.path.join(SEED_DATA_PATH, "documents")
    
    documents_data = [
        {
            "filename": "corporate_law_ru.txt",
            "title": "Основные положения корпоративного права РФ",
            "document_type": "external_law",
            "jurisdiction": "RU",
            "practice_area": "Corporate"
        },
        {
            "filename": "ma_practice_memo.txt",
            "title": "Внутреннее мемо: Основные этапы сделки M&A",
            "document_type": "memo",
            "jurisdiction": "INTERNAL",
            "practice_area": "M&A"
        },
        {
            "filename": "uk_contract_law.txt",
            "title": "Principles of UK Contract Law",
            "document_type": "external_law",
            "jurisdiction": "UK",
            "practice_area": "Corporate"
        },
        {
            "filename": "court_practice_ru.txt",
            "title": "Обзор судебной практики по корпоративным спорам",
            "document_type": "case_law",
            "jurisdiction": "RU",
            "practice_area": "Litigation"
        }
    ]
    
    created_docs = []
    
    for doc_data in documents_data:
        file_path = os.path.join(documents_dir, doc_data["filename"])
        
        existing = db.query(Document).filter(Document.title == doc_data["title"]).first()
        if existing:
            print(f"  Document already exists: {doc_data['title']}")
            continue
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            document = Document(
                title=doc_data["title"],
                document_type=doc_data["document_type"],
                jurisdiction=doc_data["jurisdiction"],
                practice_area=doc_data["practice_area"],
                content=content,
                indexing_status="pending"
            )
            db.add(document)
            db.flush()
            created_docs.append(document.id)
            print(f"  Created document: {doc_data['title']}")
        else:
            print(f"  File not found: {file_path}")
    
    db.commit()
    return created_docs


def create_templates(db: Session):
    """Create demo templates."""
    print("Creating templates...")
    
    templates_data = [
        {
            "name": "NDA (Соглашение о конфиденциальности)",
            "description": "Стандартное соглашение о неразглашении конфиденциальной информации",
            "category": "nda",
            "jurisdiction": "RU",
            "form_schema": {
                "fields": [
                    {"name": "party1", "type": "text", "label": "Раскрывающая сторона", "required": True},
                    {"name": "party2", "type": "text", "label": "Получающая сторона", "required": True},
                    {"name": "subject", "type": "textarea", "label": "Предмет раскрытия", "required": True},
                    {"name": "term", "type": "text", "label": "Срок действия", "required": True, "default": "3 (три) года"},
                    {"name": "governing_law", "type": "select", "label": "Применимое право", "required": True, "options": ["Российской Федерации", "Англии и Уэльса", "Штата Нью-Йорк"]}
                ]
            },
            "optional_sections": ["arbitration_clause", "liquidated_damages"]
        },
        {
            "name": "SPA (Договор купли-продажи долей) - упрощённый",
            "description": "Упрощённая форма договора купли-продажи акций/долей",
            "category": "spa",
            "jurisdiction": "RU",
            "form_schema": {
                "fields": [
                    {"name": "seller", "type": "text", "label": "Продавец", "required": True},
                    {"name": "buyer", "type": "text", "label": "Покупатель", "required": True},
                    {"name": "company", "type": "text", "label": "Компания (объект сделки)", "required": True},
                    {"name": "shares", "type": "text", "label": "Размер доли/акций", "required": True, "default": "100%"},
                    {"name": "price", "type": "text", "label": "Цена сделки", "required": True},
                    {"name": "payment_terms", "type": "textarea", "label": "Условия оплаты", "required": False}
                ]
            },
            "optional_sections": ["representations", "indemnification", "non_compete"]
        },
        {
            "name": "Трудовой договор (упрощённый)",
            "description": "Базовая форма трудового договора",
            "category": "employment",
            "jurisdiction": "RU",
            "form_schema": {
                "fields": [
                    {"name": "employer", "type": "text", "label": "Работодатель", "required": True},
                    {"name": "employee", "type": "text", "label": "Работник (ФИО)", "required": True},
                    {"name": "position", "type": "text", "label": "Должность", "required": True},
                    {"name": "salary", "type": "text", "label": "Оклад (в месяц)", "required": True},
                    {"name": "start_date", "type": "date", "label": "Дата начала работы", "required": True},
                    {"name": "probation", "type": "checkbox", "label": "Испытательный срок (3 месяца)", "required": False}
                ]
            },
            "optional_sections": ["non_disclosure", "non_compete"]
        }
    ]
    
    for tmpl_data in templates_data:
        existing = db.query(Template).filter(Template.name == tmpl_data["name"]).first()
        if existing:
            print(f"  Template already exists: {tmpl_data['name']}")
            continue
        
        template = Template(
            name=tmpl_data["name"],
            description=tmpl_data["description"],
            category=tmpl_data["category"],
            jurisdiction=tmpl_data["jurisdiction"],
            file_path="",  # No physical file, generated from form
            form_schema=tmpl_data["form_schema"],
            optional_sections=tmpl_data["optional_sections"]
        )
        db.add(template)
        print(f"  Created template: {tmpl_data['name']}")
    
    db.commit()


def create_clauses(db: Session):
    """Create demo clauses."""
    print("Creating clauses...")
    
    clauses_data = [
        {
            "title": "Арбитражная оговорка (ICC)",
            "category": "arbitration",
            "jurisdiction": "INTERNAL",
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Все споры, разногласия или требования, возникающие из настоящего договора или в связи с ним, в том числе касающиеся его исполнения, нарушения, прекращения или недействительности, подлежат разрешению в Международном арбитражном суде Международной торговой палаты (ICC) в соответствии с Арбитражным регламентом этого суда.

Место арбитража: [город]
Язык арбитражного разбирательства: русский
Количество арбитров: один / три""",
            "tags": ["international", "standard"],
            "notes": "Стандартная арбитражная оговорка ICC для международных контрактов"
        },
        {
            "title": "Арбитражная оговорка (МКАС при ТПП РФ)",
            "category": "arbitration",
            "jurisdiction": "RU",
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Все споры, разногласия или требования, возникающие из настоящего договора или в связи с ним, в том числе касающиеся его исполнения, нарушения, прекращения или недействительности, подлежат разрешению в Международном коммерческом арбитражном суде при Торгово-промышленной палате Российской Федерации в соответствии с его Регламентом.

Место арбитража: г. Москва
Язык арбитражного разбирательства: русский""",
            "tags": ["domestic", "standard"],
            "notes": "Арбитражная оговорка для споров с российским элементом"
        },
        {
            "title": "Форс-мажор (расширенная формулировка)",
            "category": "force_majeure",
            "jurisdiction": None,
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Ни одна из Сторон не несёт ответственности за полное или частичное неисполнение обязательств по настоящему Договору, если такое неисполнение явилось следствием обстоятельств непреодолимой силы, возникших после заключения настоящего Договора в результате событий чрезвычайного характера, которые Сторона не могла ни предвидеть, ни предотвратить разумными мерами.

К обстоятельствам непреодолимой силы относятся: война, военные действия, террористические акты, эпидемии, пандемии, землетрясения, наводнения, пожары и иные стихийные бедствия, забастовки, действия государственных органов, изменения законодательства, делающие исполнение невозможным, и иные обстоятельства, находящиеся вне разумного контроля Сторон.

Сторона, для которой создалась невозможность исполнения обязательств, обязана в течение [10] рабочих дней уведомить другую Сторону о наступлении и прекращении таких обстоятельств.""",
            "tags": ["standard", "balanced"],
            "notes": "Расширенная формулировка с учётом пандемии"
        },
        {
            "title": "Конфиденциальность (стандартная)",
            "category": "confidentiality",
            "jurisdiction": "RU",
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Стороны обязуются сохранять конфиденциальность всей информации, полученной в связи с заключением и исполнением настоящего Договора, включая, но не ограничиваясь: условия Договора, коммерческую, техническую, финансовую информацию, персональные данные.

Обязательства по сохранению конфиденциальности не распространяются на информацию:
(а) которая является или станет общедоступной не по вине получающей Стороны;
(б) которая была известна получающей Стороне до её получения от другой Стороны;
(в) которая получена от третьих лиц, не связанных обязательством конфиденциальности;
(г) раскрытие которой требуется в силу закона или по требованию уполномоченных государственных органов.

Обязательства по сохранению конфиденциальности действуют в течение [5] лет после прекращения действия настоящего Договора.""",
            "tags": ["standard"],
            "notes": "Базовое положение о конфиденциальности"
        },
        {
            "title": "Ограничение ответственности",
            "category": "liability",
            "jurisdiction": None,
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Совокупная ответственность каждой из Сторон по настоящему Договору, включая ответственность за нарушение заверений и гарантий, не может превышать [сумму] / [__]% от цены Договора.

Ни одна из Сторон не несёт ответственности за упущенную выгоду, потерю деловой репутации, косвенные или случайные убытки другой Стороны.

Настоящие ограничения не применяются к:
(а) умышленным нарушениям;
(б) нарушениям обязательств по конфиденциальности;
(в) требованиям третьих лиц, за которые предусмотрено возмещение.""",
            "tags": ["balanced", "buyer_friendly"],
            "notes": "Стандартное ограничение ответственности с cap"
        },
        {
            "title": "Существенное неблагоприятное изменение (MAC)",
            "category": "representations",
            "jurisdiction": None,
            "practice_area": "M&A",
            "language": "ru",
            "body": """Покупатель вправе отказаться от исполнения настоящего Договора без выплаты компенсации в случае наступления Существенного неблагоприятного изменения (Material Adverse Change).

Под Существенным неблагоприятным изменением понимается любое событие, обстоятельство или изменение, которое отдельно или в совокупности с другими событиями оказывает или может оказать существенное неблагоприятное воздействие на:
(а) бизнес, активы, финансовое состояние или результаты деятельности Компании;
(б) способность Продавца исполнить обязательства по настоящему Договору.

Существенным неблагоприятным изменением не признаются:
(а) общие изменения экономической или политической ситуации;
(б) изменения, затрагивающие отрасль в целом;
(в) изменения, вызванные объявлением о сделке;
(г) изменения законодательства общего применения.""",
            "tags": ["buyer_friendly", "ma"],
            "notes": "MAC clause для M&A сделок"
        },
        {
            "title": "Применимое право и юрисдикция (Россия)",
            "category": "governing_law",
            "jurisdiction": "RU",
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Настоящий Договор регулируется и толкуется в соответствии с материальным правом Российской Федерации.

Все споры, возникающие из настоящего Договора или в связи с ним, подлежат рассмотрению в Арбитражном суде города Москвы.""",
            "tags": ["standard", "domestic"],
            "notes": "Российское право и суды"
        },
        {
            "title": "Применимое право и юрисдикция (Англия)",
            "category": "governing_law",
            "jurisdiction": "UK",
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Настоящий Договор регулируется и толкуется в соответствии с правом Англии и Уэльса.

Стороны безоговорочно соглашаются с исключительной юрисдикцией судов Англии и Уэльса в отношении любых споров, возникающих из настоящего Договора или в связи с ним.""",
            "tags": ["international", "standard"],
            "notes": "Английское право для международных контрактов"
        },
        {
            "title": "Возмещение убытков (Indemnification)",
            "category": "indemnification",
            "jurisdiction": None,
            "practice_area": "M&A",
            "language": "ru",
            "body": """Продавец обязуется возместить Покупателю и освободить его от ответственности в отношении любых убытков, расходов, обязательств, требований и издержек (включая разумные расходы на юридическую помощь), возникших в результате:

(а) нарушения Продавцом любого заверения или гарантии, содержащихся в настоящем Договоре;
(б) нарушения Продавцом любого обязательства по настоящему Договору;
(в) требований третьих лиц, основанных на событиях, произошедших до Даты закрытия.

Право на возмещение возникает при условии, что:
(i) общая сумма убытков превышает [___] рублей (порог существенности);
(ii) требование о возмещении заявлено в течение [18/24] месяцев с Даты закрытия.""",
            "tags": ["ma", "buyer_friendly"],
            "notes": "Indemnification clause для M&A с порогами"
        },
        {
            "title": "Расторжение договора",
            "category": "termination",
            "jurisdiction": "RU",
            "practice_area": "Corporate",
            "language": "ru",
            "body": """Настоящий Договор может быть расторгнут:

(а) по соглашению Сторон в любое время;

(б) любой Стороной в одностороннем внесудебном порядке в случае существенного нарушения другой Стороной условий Договора, если такое нарушение не устранено в течение [30] дней с момента получения письменного уведомления о нарушении;

(в) любой Стороной в случае введения в отношении другой Стороны процедуры банкротства или ликвидации;

(г) любой Стороной при наступлении обстоятельств непреодолимой силы, продолжающихся более [90] дней.

При расторжении Договора Стороны производят взаиморасчёты в течение [30] дней.""",
            "tags": ["standard", "balanced"],
            "notes": "Стандартные основания для расторжения"
        }
    ]
    
    for clause_data in clauses_data:
        existing = db.query(Clause).filter(Clause.title == clause_data["title"]).first()
        if existing:
            print(f"  Clause already exists: {clause_data['title']}")
            continue
        
        clause = Clause(
            title=clause_data["title"],
            category=clause_data["category"],
            jurisdiction=clause_data.get("jurisdiction"),
            practice_area=clause_data.get("practice_area"),
            language=clause_data.get("language", "ru"),
            body=clause_data["body"],
            tags=clause_data.get("tags"),
            notes=clause_data.get("notes")
        )
        db.add(clause)
        print(f"  Created clause: {clause_data['title']}")
    
    db.commit()


async def index_documents(document_ids: list):
    """Index documents for semantic search."""
    print("Indexing documents...")
    
    for doc_id in document_ids:
        print(f"  Indexing document {doc_id}...")
        await IndexingService.index_document(doc_id)
    
    print("  Indexing complete!")


def main():
    """Main seed function."""
    print("=" * 50)
    print("Legal AI System - Seed Script")
    print("=" * 50)
    
    # Create tables if they don't exist
    print("\nInitializing database...")
    Base.metadata.create_all(bind=engine)
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create seed data
        create_users(db)
        document_ids = create_documents(db)
        create_templates(db)
        create_clauses(db)
        
        # Index documents
        if document_ids:
            asyncio.run(index_documents(document_ids))
        
        print("\n" + "=" * 50)
        print("Seed completed successfully!")
        print("=" * 50)
        print("\nDemo credentials:")
        print("  Admin: admin@example.com / password123")
        print("  Lawyer: lawyer@example.com / password123")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError during seed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

