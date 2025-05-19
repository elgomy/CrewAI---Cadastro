import os
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from supabase import create_client, Client as SupabaseClient
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Usar la service_role key para acceso directo

class SupabaseDocumentContentSchema(BaseModel):
    """Input schema for SupabaseDocumentContentTool."""
    document_name: str = Field(description="The exact name of the document (e.g., 'checklist.pdf', '1- CNPJ.pdf') to retrieve from the 'documents' table in Supabase.")

class SupabaseDocumentContentTool(BaseTool):
    name: str = "Supabase Document Content Retriever"
    description: str = "Retrieves the pre-parsed text content of a specific document stored in the 'documents' table in Supabase based on its name."
    args_schema: Type[BaseModel] = SupabaseDocumentContentSchema
    supabase_client: Optional[SupabaseClient] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            logger.error("Supabase URL ou Service Key não configurados nas variáveis de ambiente.")
            raise ValueError("Supabase URL or Service Key not configured for SupabaseDocumentContentTool.")
        try:
            self.supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            logger.info("Cliente Supabase inicializado para SupabaseDocumentContentTool.")
        except Exception as e:
            logger.error(f"Falha ao inicializar cliente Supabase para SupabaseDocumentContentTool: {e}")
            self.supabase_client = None # Garantir que está None se falhar

    def _run(self, document_name: str) -> str:
        if not self.supabase_client:
            return "Error: Supabase client not initialized."
        try:
            logger.info(f"Recuperando conteúdo para o documento: '{document_name}' da tabela 'documents'.")
            response = (
                self.supabase_client.table("documents")
                .select("content")
                .eq("name", document_name)
                .limit(1)
                .execute()
            )
            
            if response.data:
                content = response.data[0].get("content")
                if content:
                    logger.info(f"Conteúdo encontrado para '{document_name}'. Tamanho: {len(content)}")
                    return str(content) # Garantir que é string
                else:
                    logger.warning(f"Documento '{document_name}' encontrado mas não possui conteúdo (content is null/empty).")
                    return f"Error: Document '{document_name}' found but has no content."
            else:
                logger.warning(f"Nenhum documento encontrado com o nome '{document_name}' na tabela 'documents'.")
                return f"Error: No document found with name '{document_name}'."

        except Exception as e:
            logger.error(f"Erro ao consultar a tabela 'documents' no Supabase para '{document_name}': {e}")
            return f"Error querying Supabase for document '{document_name}': {str(e)}"

# Exemplo de uso (para teste local, se necessário):
# if __name__ == '__main__':
#     # Certifique-se que SUPABASE_URL e SUPABASE_SERVICE_KEY estão no seu .env
#     tool = SupabaseDocumentContentTool()
#     # Substitua pelo nome de um documento que exista na sua tabela
#     doc_name_to_test = "checklist.pdf" 
#     content = tool._run(document_name=doc_name_to_test)
#     print(f"Conteúdo para '{doc_name_to_test}':\n{content[:500]}...") # Imprime os primeiros 500 caracteres 