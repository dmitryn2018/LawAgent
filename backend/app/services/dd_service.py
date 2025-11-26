import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.due_diligence import DueDiligenceCheck
from app.providers.llm_provider import get_llm_provider


class DueDiligenceService:
    """Service for due diligence check operations."""
    
    @staticmethod
    async def run_check(check_id: int):
        """Run a due diligence check."""
        db = SessionLocal()
        try:
            check = db.query(DueDiligenceCheck).filter(DueDiligenceCheck.id == check_id).first()
            if not check:
                logger.error(f"DD check {check_id} not found")
                return
            
            # Update status
            check.status = "processing"
            db.commit()
            
            # Load seed data
            raw_data = DueDiligenceService._load_seed_data(check.company_name, check.jurisdiction)
            check.raw_data = raw_data
            
            # Generate AI summary
            summary, risk_indicators, risk_items = await DueDiligenceService._generate_analysis(
                check.company_name,
                check.check_type,
                check.jurisdiction,
                raw_data
            )
            
            check.ai_summary = summary
            check.risk_indicators = risk_indicators
            check.risk_items = risk_items
            check.status = "completed"
            check.completed_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"DD check {check_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error running DD check {check_id}: {e}")
            try:
                check = db.query(DueDiligenceCheck).filter(DueDiligenceCheck.id == check_id).first()
                if check:
                    check.status = "failed"
                    check.error_message = str(e)
                    db.commit()
            except:
                pass
        finally:
            db.close()
    
    @staticmethod
    def _load_seed_data(company_name: str, jurisdiction: str) -> Dict[str, Any]:
        """Load seed data for demo purposes."""
        # Get seed path relative to this file (works in both Docker and local)
        # File is at: /app/app/services/dd_service.py (Docker) or backend/app/services/dd_service.py (local)
        # seed-data is at: /app/seed-data (Docker) or seed-data (local, at repo root)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        seed_path = os.path.join(current_dir, "..", "..", "seed-data", "dd")
        seed_path = os.path.normpath(seed_path)
        
        logger.info(f"Looking for DD seed data in: {seed_path}")
        logger.info(f"Company name: {company_name}")
        
        # Try to find matching seed file by checking file contents
        if os.path.exists(seed_path):
            seed_files = [f for f in os.listdir(seed_path) if f.endswith(".json")]
            logger.info(f"Found seed files: {seed_files}")
            
            # First, try to match by company name in file content
            for seed_file in seed_files:
                file_path = os.path.join(seed_path, seed_file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        file_company_name = data.get("company_info", {}).get("name", "")
                        # Check if input matches the company name in file
                        if company_name.lower() in file_company_name.lower() or \
                           file_company_name.lower() in company_name.lower():
                            logger.info(f"Matched by content: {seed_file} (company: {file_company_name})")
                            return data
                except Exception as e:
                    logger.warning(f"Error reading {seed_file}: {e}")
            
            # Fallback: match by filename (for simple names like "testcorp", "riskcompany")
            normalized_name = company_name.lower().replace(" ", "").replace("_", "")
            for seed_file in seed_files:
                file_base = seed_file.replace(".json", "").lower()
                if normalized_name in file_base or file_base in normalized_name:
                    file_path = os.path.join(seed_path, seed_file)
                    logger.info(f"Matched by filename: {seed_file}")
                    with open(file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
        else:
            logger.warning(f"Seed path does not exist: {seed_path}")
        
        # Return default demo data if no specific file found
        logger.info("No matching seed file found, using demo data")
        return DueDiligenceService._generate_demo_data(company_name, jurisdiction)
    
    @staticmethod
    def _generate_demo_data(company_name: str, jurisdiction: str) -> Dict[str, Any]:
        """Generate demo data for testing."""
        return {
            "company_info": {
                "name": company_name,
                "inn": "7701234567",
                "ogrn": "1027700123456",
                "registration_date": "2015-03-15",
                "legal_address": "г. Москва, ул. Примерная, д. 1",
                "authorized_capital": "10 000 000 руб.",
                "status": "Действующее"
            },
            "court_cases": [
                {
                    "case_number": "А40-12345/2023",
                    "court": "Арбитражный суд г. Москвы",
                    "role": "Ответчик",
                    "claim_amount": "5 000 000 руб.",
                    "status": "Рассматривается",
                    "subject": "Взыскание задолженности по договору поставки"
                },
                {
                    "case_number": "А40-67890/2022",
                    "court": "Арбитражный суд г. Москвы",
                    "role": "Истец",
                    "claim_amount": "2 500 000 руб.",
                    "status": "Удовлетворено",
                    "subject": "Взыскание дебиторской задолженности"
                }
            ],
            "debts": {
                "tax_debt": "0 руб.",
                "social_fund_debt": "0 руб.",
                "enforcement_proceedings": []
            },
            "licenses": [
                {
                    "type": "Лицензия на осуществление строительной деятельности",
                    "number": "ГС-1-77-01-26-0-7701234567-012345-1",
                    "valid_until": "2025-12-31",
                    "status": "Действует"
                }
            ],
            "regions": ["Москва", "Московская область", "Санкт-Петербург"],
            "sanctions_flags": {
                "ofac_list": False,
                "eu_sanctions": False,
                "un_sanctions": False,
                "national_list": False
            },
            "beneficial_owners": [
                {
                    "name": "Иванов Иван Иванович",
                    "share": "60%",
                    "position": "Генеральный директор"
                },
                {
                    "name": "Петров Пётр Петрович",
                    "share": "40%",
                    "position": "Учредитель"
                }
            ]
        }
    
    @staticmethod
    async def _generate_analysis(
        company_name: str,
        check_type: str,
        jurisdiction: str,
        raw_data: Dict[str, Any]
    ) -> tuple:
        """Generate AI analysis of the collected data."""
        llm_provider = get_llm_provider()
        
        check_type_name = "M&A Due Diligence" if check_type == "ma_dd" else "Комплаенс-проверка"
        
        prompt = f"""Проведи {check_type_name} для компании "{company_name}" (юрисдикция: {jurisdiction}) на основе следующих данных:

ИНФОРМАЦИЯ О КОМПАНИИ:
{json.dumps(raw_data.get('company_info', {}), ensure_ascii=False, indent=2)}

СУДЕБНЫЕ ДЕЛА:
{json.dumps(raw_data.get('court_cases', []), ensure_ascii=False, indent=2)}

ЗАДОЛЖЕННОСТИ:
{json.dumps(raw_data.get('debts', {}), ensure_ascii=False, indent=2)}

ЛИЦЕНЗИИ:
{json.dumps(raw_data.get('licenses', []), ensure_ascii=False, indent=2)}

САНКЦИОННЫЕ ПРОВЕРКИ:
{json.dumps(raw_data.get('sanctions_flags', {}), ensure_ascii=False, indent=2)}

БЕНЕФИЦИАРЫ:
{json.dumps(raw_data.get('beneficial_owners', []), ensure_ascii=False, indent=2)}

Составь структурированный отчёт со следующими разделами:
1. ОБЩАЯ ИНФОРМАЦИЯ О КОМПАНИИ
2. СУДЕБНЫЕ СПОРЫ И ПРАВОВЫЕ РИСКИ
3. ФИНАНСОВЫЕ РИСКИ
4. РЕГУЛЯТОРНЫЕ РИСКИ
5. ОБЩИЕ ВЫВОДЫ И РЕКОМЕНДАЦИИ

Для каждого раздела укажи уровень риска (низкий/средний/высокий).
"""
        
        summary = await llm_provider.generate(
            prompt=prompt,
            system_prompt="Вы - опытный юрист, специализирующийся на due diligence. Давайте объективные и структурированные оценки.",
            temperature=0.5,
            max_tokens=2500
        )
        
        # Analyze risk levels based on data
        risk_indicators = DueDiligenceService._calculate_risk_indicators(raw_data)
        risk_items = DueDiligenceService._extract_risk_items(raw_data)
        
        return summary, risk_indicators, risk_items
    
    @staticmethod
    def _calculate_risk_indicators(raw_data: Dict[str, Any]) -> Dict[str, str]:
        """Calculate risk indicators from raw data."""
        legal_risk = "low"
        financial_risk = "low"
        regulatory_risk = "low"
        
        # Analyze court cases
        court_cases = raw_data.get("court_cases", [])
        if len(court_cases) > 3:
            legal_risk = "high"
        elif len(court_cases) > 0:
            legal_risk = "medium"
        
        # Analyze debts
        debts = raw_data.get("debts", {})
        if debts.get("enforcement_proceedings"):
            financial_risk = "high"
        elif debts.get("tax_debt", "0") != "0" or debts.get("tax_debt", "0 руб.") != "0 руб.":
            financial_risk = "medium"
        
        # Analyze sanctions
        sanctions = raw_data.get("sanctions_flags", {})
        if any(sanctions.values()):
            regulatory_risk = "high"
        
        # Calculate overall risk
        risks = [legal_risk, financial_risk, regulatory_risk]
        if "high" in risks:
            overall = "high"
        elif "medium" in risks:
            overall = "medium"
        else:
            overall = "low"
        
        return {
            "overall": overall,
            "legal": legal_risk,
            "financial": financial_risk,
            "regulatory": regulatory_risk
        }
    
    @staticmethod
    def _extract_risk_items(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract specific risk items from raw data."""
        items = []
        
        # Court case risks
        for case in raw_data.get("court_cases", []):
            if case.get("role") == "Ответчик":
                # Determine impact_on_deal based on claim amount
                claim_str = case.get("claim_amount", "0")
                try:
                    claim_amount = int("".join(filter(str.isdigit, claim_str)))
                except:
                    claim_amount = 0
                
                impact = "negotiable"
                if claim_amount > 10_000_000:  # > 10M RUB
                    impact = "deal_breaker"
                elif claim_amount < 1_000_000:  # < 1M RUB
                    impact = "cosmetic"
                
                items.append({
                    "category": "legal",
                    "severity": "medium",
                    "title": f"Судебное дело {case.get('case_number', 'N/A')}",
                    "description": f"{case.get('subject', 'N/A')}. Сумма иска: {case.get('claim_amount', 'N/A')}",
                    "impact_on_deal": impact
                })
        
        # Debt risks
        debts = raw_data.get("debts", {})
        for proc in debts.get("enforcement_proceedings", []):
            # Format enforcement proceeding description properly
            if isinstance(proc, dict):
                desc_parts = []
                if proc.get("number"):
                    desc_parts.append(f"№ {proc['number']}")
                if proc.get("amount"):
                    desc_parts.append(f"Сумма: {proc['amount']}")
                if proc.get("type"):
                    desc_parts.append(f"Тип: {proc['type']}")
                if proc.get("status"):
                    desc_parts.append(f"Статус: {proc['status']}")
                description = ". ".join(desc_parts)
            else:
                description = str(proc)
            
            items.append({
                "category": "financial",
                "severity": "high",
                "title": "Исполнительное производство",
                "description": description,
                "impact_on_deal": "deal_breaker"  # Enforcement proceedings are always critical
            })
        
        # Sanctions risks
        sanctions = raw_data.get("sanctions_flags", {})
        for key, value in sanctions.items():
            if value:
                items.append({
                    "category": "regulatory",
                    "severity": "high",
                    "title": f"Санкционный список: {key}",
                    "description": "Компания или её бенефициары находятся в санкционном списке",
                    "impact_on_deal": "deal_breaker"  # Sanctions are always deal-breakers
                })
        
        return items

