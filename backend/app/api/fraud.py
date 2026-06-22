from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.core.database import get_db
from api.auth import get_current_user
from src.models.db_models import Transaction, AuditLog
from models.fraud_alert import FraudAlert
from src.tools.analysis import detect_anomalies_tool
from datetime import datetime

router = APIRouter(prefix="/fraud", tags=["Fraud"])

@router.get("")
async def list_fraud_alerts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch on-the-fly anomalies
    res = await detect_anomalies_tool(db)
    if res.get("status") == "success":
        anoms = res["data"].get("anomalies", [])
        
        for anom in anoms:
            # Check if this anomaly is already saved in FraudAlert table
            stmt = select(FraudAlert).where(FraudAlert.transaction_id == anom["transaction_id"])
            existing_res = await db.execute(stmt)
            existing = existing_res.scalar_one_or_none()
            
            if not existing:
                risk = anom.get("risk_score", 50.0)
                severity = "High" if risk >= 75.0 else "Medium"
                reasons_str = "; ".join(anom.get("reasons", ["Anomalous transaction value pattern detected"]))
                
                alert_obj = FraudAlert(
                    transaction_id=anom["transaction_id"],
                    is_resolved=False,
                    severity=severity,
                    reason=reasons_str,
                    risk_score=risk,
                    detected_at=datetime.utcnow()
                )
                db.add(alert_obj)
        await db.commit()

    # 2. Query all fraud alerts
    stmt = select(FraudAlert).order_by(FraudAlert.is_resolved, FraudAlert.detected_at.desc())
    res = await db.execute(stmt)
    alerts = res.scalars().all()
    
    out = []
    for a in alerts:
        # Load transaction details
        tx_stmt = select(Transaction).where(Transaction.transaction_id == a.transaction_id)
        tx_res = await db.execute(tx_stmt)
        tx = tx_res.scalar_one_or_none()
        
        out.append({
            "id": a.id,
            "is_resolved": a.is_resolved,
            "severity": a.severity,
            "reason": a.reason,
            "detected_at": a.detected_at.isoformat(),
            "risk_score": a.risk_score,
            "transaction": {
                "merchant": tx.merchant if tx else "Unknown Merchant",
                "amount": tx.amount if tx else 0.0
            }
        })
    return out

@router.post("/resolve/{alertId}")
async def resolve_fraud_alert(
    alertId: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(FraudAlert).where(FraudAlert.id == alertId)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Fraud alert not found.")
        
    alert.is_resolved = True
    
    # Audit log
    audit = AuditLog(
        action="FRAUD_ALERT_RESOLVED",
        agent="fraud_monitor",
        status="SUCCESS",
        details=f"Anomalous transaction {alert.transaction_id} marked as resolved."
    )
    db.add(audit)
    await db.commit()
    
    return {"message": f"Alert {alertId} successfully resolved."}
