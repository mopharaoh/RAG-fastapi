from .BaseController import BaseController
from models import ResponseSignal
from models.db_schemes import Project, DataChunk
from typing import List
from stores.llm.LLMEnums import DocumentTypeEnum
import json

class NLPController(BaseController):

    def __init__(self, vectordb_client, generation_client, embedding_client):
        super().__init__()

        self.vectordb_client = vectordb_client
        self.generation_client = generation_client
        self.embedding_client = embedding_client

    def create_collection_name(self,project_id: str):
        return f"collection_{project_id}".strip()
    
    def reset_vectordb_collection(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.id)
        self.vectordb_client.delete_collection(collection_name=collection_name)

    def get_vector_db_collection_info(self, project: Project):
        collection_name = self.create_collection_name(project_id=project.id)
        collection_info = self.vectordb_client.get_collection_info(collection_name=collection_name)

        return json.loads(
            json.dumps(collection_info, default = lambda x: x.__dict__)
        )
    
    def index_into_vectordb(self, project: Project , chunks: List[DataChunk],
                            chunks_ids: List[int],
                            do_reset: bool=None):
        collection_name = self.create_collection_name(project_id=project.id)
        
        texts = [ c.chunk_text for c in chunks]
        metadata = [ c.chunk_metadata for c in chunks ]

        vectors = [
            self.embedding_client.embed_text(
                text=text,
                document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts
        ]
        _ = self.vectordb_client.create_collection(collection_name=collection_name,
                                                   embedding_size=self.embedding_client.embedding_size,
                                                   do_reset=do_reset)
        _ = self.vectordb_client.insert_many(
            collection_name=collection_name,
            texts=texts,
            metadata=metadata,
            vectors=vectors,
            record_ids=chunks_ids
        )

        return True 
    
    def search_vector_db_collection(self, project: Project, text: str, limit: int=10):
        collection_name = self.create_collection_name(project_id=project.id)
        vector = self.embedding_client.embed_text(text,document_type=DocumentTypeEnum.QUERY.value)

        if not vector or len(vector) == 0:
            return False
        
        results = self.vectordb_client.search_by_vector(
            collection_name=collection_name,
            vector=vector,
            limit=limit
        )

        if not results:
            return False

        return json.loads(
            json.dumps(results, default=lambda x : x.__dict__)
        )