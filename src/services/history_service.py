import json
from datetime import date, datetime, time

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import FeedItem, FetchBatch, Source
from src.schemas.history import HistoryBatch, HistoryBatchesResponse, HistoryItem, PaginationInfo


class HistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_history_batches(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> HistoryBatchesResponse:
        count_query = select(func.count()).select_from(FetchBatch)
        total_result = await self.session.execute(count_query)
        total_batches = total_result.scalar() or 0

        items_query = select(func.count()).select_from(FeedItem).where(
            FeedItem.batch_id.isnot(None)
        )
        items_result = await self.session.execute(items_query)
        total_items = items_result.scalar() or 0

        query = (
            select(FetchBatch)
            .order_by(FetchBatch.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        batches = list(result.scalars().all())

        batch_list = []
        for batch in batches:
            sources: list[str] = []
            if batch.sources:
                try:
                    sources = json.loads(batch.sources)
                except (json.JSONDecodeError, TypeError):
                    sources = []

            batch_list.append(
                HistoryBatch(
                    id=batch.id,
                    items_count=batch.items_count,
                    sources=sources,
                    created_at=batch.created_at.isoformat() if batch.created_at else "",
                )
            )

        return HistoryBatchesResponse(
            batches=batch_list,
            total_batches=total_batches,
            total_items=total_items,
        )

    async def get_history_by_batch(
        self,
        batch_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[HistoryItem], PaginationInfo]:
        query = (
            select(FeedItem)
            .options(joinedload(FeedItem.source))
            .where(
                FeedItem.batch_id == batch_id,
                FeedItem.deleted_at.is_(None),
            )
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar() or 0

        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        offset = (page - 1) * page_size

        query = query.order_by(FeedItem.fetched_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.unique().scalars().all())

        return [
            HistoryItem(
                id=item.id,
                source_id=item.source_id,
                source=item.source.name if item.source else "",
                title=item.title,
                link=item.link,
                description=item.description or "",
                published_at=item.published_at.isoformat() if item.published_at else None,
                fetched_at=item.fetched_at.isoformat() if item.fetched_at else None,
            )
            for item in items
        ], PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    async def get_history(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        source_ids: list[int] | None = None,
        keywords: str | None = None,
        sort_by: str = "fetched_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HistoryItem], PaginationInfo]:
        query = (
            select(FeedItem)
            .options(joinedload(FeedItem.source))
            .where(
                FeedItem.deleted_at.is_(None),
                FeedItem.source.has(Source.is_active == True),
                FeedItem.source.has(Source.deleted_at.is_(None)),
            )
        )

        if start_date is not None:
            start_datetime = datetime.combine(start_date, time.min)
            query = query.where(FeedItem.fetched_at >= start_datetime)

        if end_date is not None:
            end_datetime = datetime.combine(end_date, time.max)
            query = query.where(FeedItem.fetched_at <= end_datetime)

        if source_ids:
            query = query.where(FeedItem.source_id.in_(source_ids))

        if keywords:
            keyword_list = [k.strip() for k in keywords.split(";") if k.strip()]
            if keyword_list:
                conditions = [FeedItem.title.ilike(f"%{kw}%") for kw in keyword_list]
                query = query.where(or_(*conditions))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar() or 0

        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        offset = (page - 1) * page_size

        if sort_by == "published_at":
            order_col = FeedItem.published_at
        else:
            order_col = FeedItem.fetched_at

        if sort_order == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.unique().scalars().all())

        return [
            HistoryItem(
                id=item.id,
                source_id=item.source_id,
                source=item.source.name if item.source else "",
                title=item.title,
                link=item.link,
                description=item.description or "",
                published_at=item.published_at.isoformat() if item.published_at else None,
                fetched_at=item.fetched_at.isoformat() if item.fetched_at else None,
            )
            for item in items
        ], PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )