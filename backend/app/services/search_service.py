from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from app.models.document import Document, DocumentChunk
from app.schemas.document import SearchResultItem
from app.providers.embedding_provider import get_embedding_provider


class SearchService:
    """Service for semantic search operations."""
    
    @staticmethod
    async def search(
        query: str,
        jurisdiction: Optional[str] = None,
        practice_area: Optional[str] = None,
        document_type: Optional[str] = None,
        top_k: int = 10,
        db: Session = None
    ) -> List[SearchResultItem]:
        """Perform semantic search across document chunks."""
        try:
            # Get query embedding
            embedding_provider = get_embedding_provider()
            query_embedding = await embedding_provider.embed(query)
            
            # Build the query with filters
            filters = []
            params = {"top_k": top_k}
            
            # Convert embedding to PostgreSQL vector format
            embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            if jurisdiction:
                filters.append("d.jurisdiction = :jurisdiction")
                params["jurisdiction"] = jurisdiction
            if practice_area:
                filters.append("d.practice_area = :practice_area")
                params["practice_area"] = practice_area
            if document_type:
                filters.append("d.document_type = :document_type")
                params["document_type"] = document_type
            
            filter_clause = " AND ".join(filters) if filters else "1=1"
            
            # Perform vector similarity search
            sql = text(f"""
                SELECT 
                    c.id as chunk_id,
                    c.document_id,
                    c.text,
                    d.title,
                    d.document_type,
                    d.jurisdiction,
                    1 - (c.embedding <=> '{embedding_str}'::vector) as relevance
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE d.indexing_status = 'indexed'
                AND {filter_clause}
                ORDER BY c.embedding <=> '{embedding_str}'::vector
                LIMIT :top_k
            """)
            
            result = db.execute(sql, params)
            rows = result.fetchall()
            
            # Convert to response format
            results = []
            for row in rows:
                results.append(SearchResultItem(
                    document_id=row.document_id,
                    chunk_id=row.chunk_id,
                    document_title=row.title,
                    document_type=row.document_type,
                    jurisdiction=row.jurisdiction,
                    text=row.text[:500] + "..." if len(row.text) > 500 else row.text,
                    relevance=float(row.relevance) if row.relevance else 0.0
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            # Fallback to simple text search if vector search fails
            return await SearchService._fallback_search(
                query, jurisdiction, practice_area, document_type, top_k, db
            )
    
    @staticmethod
    async def _fallback_search(
        query: str,
        jurisdiction: Optional[str],
        practice_area: Optional[str],
        document_type: Optional[str],
        top_k: int,
        db: Session
    ) -> List[SearchResultItem]:
        """Fallback text-based search when vector search fails."""
        query_filter = db.query(DocumentChunk).join(Document)
        
        if jurisdiction:
            query_filter = query_filter.filter(Document.jurisdiction == jurisdiction)
        if practice_area:
            query_filter = query_filter.filter(Document.practice_area == practice_area)
        if document_type:
            query_filter = query_filter.filter(Document.document_type == document_type)
        
        # Simple LIKE search
        search_term = f"%{query}%"
        chunks = query_filter.filter(
            DocumentChunk.text.ilike(search_term)
        ).limit(top_k).all()
        
        results = []
        for chunk in chunks:
            results.append(SearchResultItem(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                document_title=chunk.document.title,
                document_type=chunk.document.document_type,
                jurisdiction=chunk.document.jurisdiction,
                text=chunk.text[:500] + "..." if len(chunk.text) > 500 else chunk.text,
                relevance=0.5  # Default relevance for text search
            ))
        
        return results

