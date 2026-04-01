import json
from datetime import date, datetime, time

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import FeedItem, FetchBatch, Source, SourceGroup, SourceGroupMember
from src.schemas.history import (
    HistoryBatch,
    HistoryBatchesResponse,
    HistoryItem,
    PaginationInfo,
    UpdateBatchNameRequest,
)


class HistoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_source_groups(self, source_id: int) -> list[dict]:
        """Fetch groups for a given source_id."""
        groups_result = await self.session.execute(
            select(SourceGroup)
            .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
            .where(SourceGroupMember.source_id == source_id)
        )
        return [{"id": g.id, "name": g.name} for g in groups_result.scalars().all()]

    def _get_batch_display_name(self, batch: FetchBatch) -> str:
        if batch.notes:
            return batch.notes
        if batch.created_at:
            return batch.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"Batch #{batch.id}"

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

            latest_fetched_at = None
            latest_published_at = None

            if batch.id:
                time_query = select(
                    func.max(FeedItem.fetched_at),
                    func.max(FeedItem.published_at)
                ).where(FeedItem.batch_id == batch.id)
                time_result = await self.session.execute(time_query)
                row = time_result.first()
                if row:
                    latest_fetched_at = row[0].isoformat() if row[0] else None
                    latest_published_at = row[1].isoformat() if row[1] else None

            # Aggregate groups from all sources in the batch
            batch_groups: list[dict] = []
            if batch.id:
                groups_result = await self.session.execute(
                    select(SourceGroup)
                    .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
                    .join(FeedItem, FeedItem.source_id == SourceGroupMember.source_id)
                    .where(FeedItem.batch_id == batch.id)
                    .distinct()
                )
                batch_groups = [
                    {"id": g.id, "name": g.name}
                    for g in groups_result.scalars().all()
                ]

            batch_list.append(
                HistoryBatch(
                    id=batch.id,
                    name=self._get_batch_display_name(batch),
                    items_count=batch.items_count,
                    sources=sources,
                    created_at=batch.created_at.isoformat() if batch.created_at else "",
                    latest_fetched_at=latest_fetched_at,
                    latest_published_at=latest_published_at,
                    groups=batch_groups,
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
            .where(FeedItem.batch_id == batch_id)
        )

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar() or 0

        total_pages = (total_items + page_size - 1) // page_size if total_items > 0 else 0
        offset = (page - 1) * page_size

        query = query.order_by(FeedItem.fetched_at.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = list(result.unique().scalars().all())

        history_items = []
        for item in items:
            source_groups = await self._get_source_groups(item.source_id)
            history_items.append(
                HistoryItem(
                    id=item.id,
                    source_id=item.source_id,
                    source=item.source.name if item.source else "",
                    title=item.title,
                    link=item.link,
                    description=item.description or "",
                    published_at=item.published_at.isoformat() if item.published_at else None,
                    fetched_at=item.fetched_at.isoformat() if item.fetched_at else None,
                    source_groups=source_groups,
                )
            )

        return history_items, PaginationInfo(
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

        history_items = []
        for item in items:
            source_groups = await self._get_source_groups(item.source_id)
            history_items.append(
                HistoryItem(
                    id=item.id,
                    source_id=item.source_id,
                    source=item.source.name if item.source else "",
                    title=item.title,
                    link=item.link,
                    description=item.description or "",
                    published_at=item.published_at.isoformat() if item.published_at else None,
                    fetched_at=item.fetched_at.isoformat() if item.fetched_at else None,
                    source_groups=source_groups,
                )
            )

        return history_items, PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        )

    async def update_batch_name(
        self,
        batch_id: int,
        request: UpdateBatchNameRequest,
    ) -> HistoryBatch | None:
        query = select(FetchBatch).where(FetchBatch.id == batch_id)
        result = await self.session.execute(query)
        batch = result.scalar_one_or_none()

        if not batch:
            return None

        update_stmt = (
            update(FetchBatch)
            .where(FetchBatch.id == batch_id)
            .values(notes=request.name)
        )
        await self.session.execute(update_stmt)
        await self.session.commit()

        await self.session.refresh(batch)

        sources: list[str] = []
        if batch.sources:
            try:
                sources = json.loads(batch.sources)
            except (json.JSONDecodeError, TypeError):
                sources = []

        latest_fetched_at = None
        latest_published_at = None

        time_query = select(
            func.max(FeedItem.fetched_at),
            func.max(FeedItem.published_at)
        ).where(FeedItem.batch_id == batch.id)
        time_result = await self.session.execute(time_query)
        row = time_result.first()
        if row:
            latest_fetched_at = row[0].isoformat() if row[0] else None
            latest_published_at = row[1].isoformat() if row[1] else None

        # Aggregate groups from all sources in the batch
        batch_groups: list[dict] = []
        if batch.id:
            groups_result = await self.session.execute(
                select(SourceGroup)
                .join(SourceGroupMember, SourceGroup.id == SourceGroupMember.group_id)
                .join(FeedItem, FeedItem.source_id == SourceGroupMember.source_id)
                .where(FeedItem.batch_id == batch.id)
                .distinct()
            )
            batch_groups = [
                {"id": g.id, "name": g.name}
                for g in groups_result.scalars().all()
            ]

        return HistoryBatch(
            id=batch.id,
            name=self._get_batch_display_name(batch),
            items_count=batch.items_count,
            sources=sources,
            created_at=batch.created_at.isoformat() if batch.created_at else "",
            latest_fetched_at=latest_fetched_at,
            latest_published_at=latest_published_at,
            groups=batch_groups,
        )

    async def delete_batch(self, batch_id: int) -> bool:
        query = select(FetchBatch).where(FetchBatch.id == batch_id)
        result = await self.session.execute(query)
        batch = result.scalar_one_or_none()

        if not batch:
            return False

        delete_stmt = delete(FetchBatch).where(FetchBatch.id == batch_id)
        await self.session.execute(delete_stmt)
        await self.session.commit()

        return True

    async def get_batch_feed_items(
        self,
        batch_id: int,
    ) -> list[HistoryItem]:
        query = (
            select(FeedItem)
            .options(joinedload(FeedItem.source))
            .where(FeedItem.batch_id == batch_id)
            .order_by(FeedItem.fetched_at.desc())
        )

        result = await self.session.execute(query)
        items = list(result.unique().scalars().all())

        history_items = []
        for item in items:
            source_groups = await self._get_source_groups(item.source_id)
            history_items.append(
                HistoryItem(
                    id=item.id,
                    source_id=item.source_id,
                    source=item.source.name if item.source else "",
                    title=item.title,
                    link=item.link,
                    description=item.description or "",
                    published_at=item.published_at.isoformat() if item.published_at else None,
                    fetched_at=item.fetched_at.isoformat() if item.fetched_at else None,
                    source_groups=source_groups,
                )
            )
        return history_items