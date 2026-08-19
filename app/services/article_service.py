# -*- coding: utf-8 -*-
"""文章业务逻辑层。"""

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleStatus
from app.models.live_code import LiveCode
from app.schemas import ArticleCreate, ArticleUpdate


class ArticleService:
    """文章 CRUD 与状态管理。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ArticleCreate) -> Article:
        article = Article(
            title=data.title,
            content=data.content,
            images=data.images or [],
            extra_fields=data.extra_fields or {},
        )
        self.session.add(article)
        await self.session.flush()
        return article

    async def get(self, article_id: int) -> Article | None:
        stmt = (
            select(Article)
            .where(Article.id == article_id, Article.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_published(self, article_id: int) -> Article | None:
        stmt = (
            select(Article)
            .where(
                Article.id == article_id,
                Article.is_deleted == False,
                Article.status == ArticleStatus.PUBLISHED.value,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, page_size: int = 20, status: str | None = None, search: str | None = None
    ) -> tuple[list[Article], int]:
        query = select(Article).where(Article.is_deleted == False)
        count_query = select(func.count(Article.id)).where(Article.is_deleted == False)

        if status:
            query = query.where(Article.status == status)
            count_query = count_query.where(Article.status == status)
        if search:
            like = f"%{search}%"
            query = query.where(Article.title.like(like))
            count_query = count_query.where(Article.title.like(like))

        # 总条数
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * page_size
        query = (
            query
            .order_by(Article.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .options(selectinload(Article.live_codes))
        )
        result = await self.session.execute(query)
        articles = list(result.scalars().all())
        return articles, total

    async def update(self, article_id: int, data: ArticleUpdate) -> Article | None:
        article = await self.get(article_id)
        if not article:
            return None
        update_data = data.model_dump(exclude_none=True)
        if update_data:
            stmt = (
                update(Article)
                .where(Article.id == article_id)
                .values(**update_data)
            )
            await self.session.execute(stmt)
            await self.session.flush()
            # 重新查询
            return await self.get(article_id)
        return article

    async def set_status(self, article_id: int, status: str) -> Article | None:
        article = await self.get(article_id)
        if not article:
            return None
        stmt = update(Article).where(Article.id == article_id).values(status=status)
        await self.session.execute(stmt)
        await self.session.flush()
        return await self.get(article_id)

    async def soft_delete(self, article_id: int) -> bool:
        article = await self.get(article_id)
        if not article:
            return False
        stmt = update(Article).where(Article.id == article_id).values(is_deleted=True)
        await self.session.execute(stmt)
        await self.session.flush()
        return True

    async def get_live_code_count(self, article_id: int) -> int:
        stmt = (
            select(func.count(LiveCode.id))
            .where(LiveCode.article_id == article_id, LiveCode.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_total_scan_count(self, article_id: int) -> int:
        stmt = (
            select(func.coalesce(func.sum(LiveCode.scan_count), 0))
            .where(LiveCode.article_id == article_id, LiveCode.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0