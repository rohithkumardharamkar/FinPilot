from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from models.report import Report
from src.tools.reporting import generate_financial_report_tool

class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_reports(self) -> list[dict]:
        stmt = select(Report).order_by(desc(Report.generated_at))
        res = await self.db.execute(stmt)
        reports = res.scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "generated_at": r.generated_at.isoformat()
            }
            for r in reports
        ]

    async def get_report_by_id(self, report_id: int) -> dict:
        stmt = select(Report).where(Report.id == report_id)
        res = await self.db.execute(stmt)
        report = res.scalar_one_or_none()
        if not report:
            raise Exception("Report not found")
        return {
            "id": report.id,
            "title": report.title,
            "content_markdown": report.content_markdown,
            "generated_at": report.generated_at.isoformat()
        }

    async def generate_report(self) -> dict:
        res = await generate_financial_report_tool(self.db)
        if res.get("status") != "success":
            raise Exception(f"Report generation tool failed: {res.get('metadata', {}).get('error', 'unknown error')}")
            
        markdown_content = res["data"]["report_content"]
        
        # Create report record
        report_title = f"Financial Health Analysis - {datetime.utcnow().strftime('%B %Y')}"
        new_report = Report(title=report_title, content_markdown=markdown_content)
        self.db.add(new_report)
        await self.db.commit()
        
        return {
            "id": new_report.id,
            "title": new_report.title,
            "content_markdown": new_report.content_markdown,
            "generated_at": new_report.generated_at.isoformat()
        }
