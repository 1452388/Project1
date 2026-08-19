# -*- coding: utf-8 -*-
"""统计 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.api.dependencies import require_registered_user
from app.schemas import StatsResponse
from app.services.live_code_service import LiveCodeService
from app.services.stats_service import StatsService

router = APIRouter(dependencies=[Depends(require_registered_user)])


@router.get("/{live_code_id}", response_model=StatsResponse)
async def get_stats(
    live_code_id: int,
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
):
    """活码统计数据（总量 + 今日 + 昨日 + 趋势）。"""
    lc_service = LiveCodeService(session)
    lc = await lc_service.get_by_id(live_code_id)
    if not lc:
        raise HTTPException(status_code=404, detail="活码不存在")

    stats = StatsService(session)
    total = await stats.get_total(live_code_id)
    today = await stats.get_today(live_code_id)
    yesterday = await stats.get_yesterday(live_code_id)
    trend = await stats.get_daily_trend(live_code_id, days=days)

    return StatsResponse(total=total, today=today, yesterday=yesterday, trend=trend)


@router.get("/{live_code_id}/export")
async def export_stats(
    live_code_id: int,
    days: int = Query(30, ge=1, le=365),
    format: str = Query("xlsx", pattern=r"^(xlsx|csv)$"),
    session: AsyncSession = Depends(get_session),
):
    """导出扫码统计数据。"""
    lc_service = LiveCodeService(session)
    lc = await lc_service.get_by_id(live_code_id)
    if not lc:
        raise HTTPException(status_code=404, detail="活码不存在")

    stats = StatsService(session)
    if format == "xlsx":
        content = await stats.export_excel(live_code_id, days=days)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"stats_{lc.code}.xlsx"
    else:
        from datetime import datetime, timedelta, timezone
        trend = await stats.get_daily_trend(live_code_id, days=days)
        import csv
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["日期", "扫码次数"])
        for item in trend:
            writer.writerow([item["date"], item["count"]])
        content = buf.getvalue().encode("utf-8-sig")
        media_type = "text/csv"
        filename = f"stats_{lc.code}.csv"

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )