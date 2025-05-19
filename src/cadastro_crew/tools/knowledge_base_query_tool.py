import os
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# Dependências para a Knowledge Base (exemplo com Supabase/pgvector e SentenceTransformers)
# pip install supabase sentence-transformers
# Lembre-se de configurar o Supabase e a extensão pgvector
from supabase import create_client, Client as SupabaseClient
from sentence_transformers import SentenceTransformer

# --- Configuração da Knowledge Base (Supabase) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") # Use a service_role key
KB_TABLE_NAME = os.getenv("KB_TABLE_NAME", "knowledge_base_chunks") # Nome da tabela no Supabase
# Modelo de embedding (escolha um bom modelo multilíngue se a KB tiver conteúdo misto)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

class KnowledgeBaseQueryToolSchema(BaseModel):
    """Define os argumentos para a ferramenta de consulta à Knowledge Base (Pydantic V2)."""
    query: str = Field(description="A pergunta ou termo de busca em linguagem natural para consultar a base de conhecimento.")
    top_k: int = Field(default=3, description="O número de resultados mais relevantes a serem retornados.")
    # Poderia adicionar filtros aqui, ex: filter_metadata: Optional[dict] = Field(default=null, description="Metadados para filtrar a busca.")

class KnowledgeBaseQueryTool(BaseTool):
    """
    Ferramenta CrewAI para consultar uma Knowledge Base (KB) implementada
    com Supabase e pgvector. Recebe uma query em linguagem natural,
    gera um embedding para ela, e busca por chunks de texto semanticamente
    similares na KB. Retorna os chunks de texto mais relevantes.
    """
    name: str = "Knowledge Base Query Tool"
    description: str = (
        "Consulta a base de conhecimento interna para encontrar informações relevantes, "
        "casos passados, políticas ou regras específicas. Use para obter contexto adicional "
        "ou respostas para perguntas que exigem conhecimento especializado armazenado."
    )
    args_schema: Type[BaseModel] = KnowledgeBaseQueryToolSchema

    _supabase_client: Optional[SupabaseClient] = None
    _embedding_model: Optional[SentenceTransformer] = None

    def __init__(self, **kwargs):
        """
        Inicializa a ferramenta, o cliente Supabase e o modelo de embedding.
        """
        super().__init__(**kwargs)
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("ALERTA: Variáveis de ambiente SUPABASE_URL e SUPABASE_SERVICE_KEY não configuradas.")
            # Poderia levantar ValueError se for um requisito estrito
            self._supabase_client = None
            self._embedding_model = None
            return

        try:
            self._supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            print("INFO: Cliente Supabase inicializado para a KnowledgeBaseQueryTool.")
        except Exception as e:
            print(f"ERRO CRÍTICO: Não foi possível inicializar o cliente Supabase: {e}")
            self._supabase_client = None

        try:
            self._embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            print(f"INFO: Modelo de embedding '{EMBEDDING_MODEL_NAME}' carregado.")
        except Exception as e:
            print(f"ERRO CRÍTICO: Não foi possível carregar o modelo de embedding '{EMBEDDING_MODEL_NAME}': {e}")
            self._embedding_model = None

    def _run(self, query: str, top_k: int = 3) -> str:
        """
        Executa a consulta na Knowledge Base.
        1. Gera o embedding da query.
        2. Executa uma stored procedure (ou query direta) no Supabase para busca por similaridade.
        3. Formata e retorna os resultados.
        """
        if not self._supabase_client or not self._embedding_model:
            return "ERRO: Ferramenta Knowledge Base não inicializada corretamente (Supabase ou Modelo de Embedding faltando)."

        if not query:
            return "ERRO: A query para a Knowledge Base não pode ser vazia."
        
        if not KB_TABLE_NAME:
            return "ERRO: Nome da tabela da Knowledge Base (KB_TABLE_NAME) não configurado."

        print(f"INFO: Recebida query para KB: '{query}', top_k={top_k}")

        try:
            # 1. Gerar embedding para a query
            print("INFO: Gerando embedding para a query...")
            query_embedding = self._embedding_model.encode(query).tolist() # type: ignore
            print("INFO: Embedding da query gerado.")

            # 2. Consultar Supabase usando uma função RPC (stored procedure) para busca de similaridade
            #    Esta função 'match_documents' (ou similar) precisaria ser criada no seu Supabase
            #    e usaria o operador de similaridade do pgvector (ex: <=>).
            #    Exemplo de função SQL no Supabase (simplificado):
            #    CREATE OR REPLACE FUNCTION match_documents (
            #      query_embedding vector(384), -- Dimensão do seu embedding_model
            #      match_threshold float,
            #      match_count int
            #    )
            #    RETURNS TABLE (
            #      id uuid,
            #      content text,
            #      similarity float,
            #      metadata jsonb -- Adicione outros campos que você armazena
            #    )
            #    LANGUAGE sql STABLE
            #    AS $$
            #      SELECT
            #        kb.id,
            #        kb.content, -- ou o nome da sua coluna de texto
            #        1 - (kb.embedding <=> query_embedding) AS similarity,
            #        kb.metadata
            #      FROM
            #        public.knowledge_base_chunks AS kb -- Nome da sua tabela
            #      WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
            #      ORDER BY
            #        similarity DESC
            #      LIMIT match_count;
            #    $$;
            
            # Nome da sua função no Supabase que faz a busca vetorial
            rpc_name = "match_kb_chunks" # Ou o nome que você der à sua função no Supabase

            print(f"INFO: Executando RPC '{rpc_name}' no Supabase...")
            response = self._supabase_client.rpc(
                rpc_name,
                params={
                    'query_embedding': query_embedding,
                    'match_threshold': 0.5,  # Ajuste este limiar conforme necessário
                    'match_count': top_k
                }
            ).execute()

            if response.data:
                print(f"INFO: {len(response.data)} resultados encontrados na KB.")
                # Formatar os resultados
                formatted_results = []
                for i, item in enumerate(response.data):
                    result_text = f"Resultado {i+1} (Similaridade: {item.get('similarity', 'N/A'):.4f}):\n"
                    result_text += f"Conteúdo: {item.get('content', 'Conteúdo não disponível')}\n"
                    if item.get('metadata'):
                        result_text += f"Metadados: {item.get('metadata')}\n"
                    result_text += "---\n"
                    formatted_results.append(result_text)
                
                if not formatted_results:
                    return "INFO: Nenhum resultado relevante encontrado na Knowledge Base para esta query."
                return "\n".join(formatted_results)
            else:
                # Isso pode acontecer se a RPC não retornar dados ou se houver um erro na RPC não capturado como exceção HTTP
                print("ALERTA: Nenhum dado retornado pela RPC do Supabase, ou a resposta não continha 'data'.")
                if hasattr(response, 'error') and response.error: # type: ignore
                    print(f"ERRO RPC Supabase: {response.error}") # type: ignore
                    return f"ERRO ao consultar KB: {response.error.message}" # type: ignore
                return "INFO: Nenhum resultado encontrado na Knowledge Base para esta query."

        except Exception as e:
            print(f"ERRO INESPERADO ao consultar a Knowledge Base: {type(e).__name__} - {e}")
            # import traceback
            # traceback.print_exc()
            return f"ERRO INTERNO DA FERRAMENTA: Falha ao consultar a Knowledge Base. Detalhes: {type(e).__name__}"

# --- Bloco de Teste Local (Conceitual) ---
if __name__ == '__main__':
    print("INFO: Iniciando teste local da KnowledgeBaseQueryTool...")

    # --- !!! IMPORTANTE: Configure suas variáveis de ambiente ANTES de rodar !!! ---
    # Exemplo (substitua com seus valores reais ou defina no seu ambiente):
    # os.environ['SUPABASE_URL'] = 'https://xxxxxxxx.supabase.co'
    # os.environ['SUPABASE_SERVICE_KEY'] = 'seu_service_role_key'
    # os.environ['KB_TABLE_NAME'] = 'knowledge_base_chunks' # ou o nome da sua tabela
    # os.environ['EMBEDDING_MODEL_NAME'] = 'sentence-transformers/all-MiniLM-L6-v2'

    if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, KB_TABLE_NAME]):
        print(("\nERRO: Variáveis de ambiente SUPABASE_URL, SUPABASE_SERVICE_KEY e KB_TABLE_NAME "
               "não configuradas. Defina-as para testar."))
        exit(1)

    kb_tool: Optional[KnowledgeBaseQueryTool] = None
    try:
        kb_tool = KnowledgeBaseQueryTool()
        if not kb_tool._supabase_client or not kb_tool._embedding_model:
            print("ERRO: Falha na inicialização da ferramenta KBTool. Verifique os logs.")
            exit(1)
    except Exception as e:
        print(f"ERRO ao instanciar a ferramenta KBTool: {e}")
        exit(1)

    print("\nINFO: Ferramenta KBTool instanciada. Lembre-se que este teste requer:")
    print(f"      1. Uma instância Supabase acessível em {SUPABASE_URL}.")
    print(f"      2. A extensão pgvector habilitada no Supabase.")
    print(f"      3. Uma tabela chamada '{KB_TABLE_NAME}' com colunas (ex: 'content' TEXT, 'embedding' VECTOR(384)).")
    print(f"      4. Uma função RPC chamada 'match_kb_chunks' (ou similar) criada no Supabase para busca vetorial.")
    print(f"      5. Dados indexados na tabela '{KB_TABLE_NAME}'.")

    queries_de_teste = [
        "Qual a política para validação de Contrato Social emitido há mais de 3 anos?",
        "casos de fraude envolvendo alteração de quadro societário",
        "documentação necessária para procurador de PJ"
    ]

    for q_idx, test_query in enumerate(queries_de_teste):
        print(f"\n--- Testando Query {q_idx + 1}: '{test_query}' ---")
        try:
            # Passando como dicionário para o método run da BaseTool
            resultado_kb = kb_tool.run({"query": test_query, "top_k": 2})
            print("\nResultado da Consulta à KB:")
            print("---------------------------")
            print(resultado_kb)
            print("---------------------------")
        except Exception as e:
            print(f"ERRO CRÍTICO durante o teste da KB: {type(e).__name__} - {e}")

    print("\nINFO: Teste local da KnowledgeBaseQueryTool concluído.") 