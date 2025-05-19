import yaml
from pathlib import Path
from crewai import Agent
from crewai_tools import SerperDevTool

# Importar ferramentas customizadas
# from .tools import LlamaParseDirectTool # Comentada/Removida se não for mais usada diretamente pelos agentes
from .tools import KnowledgeBaseQueryTool
from .tools import SupabaseDocumentContentTool # Nova ferramenta

# Carregar configurações dos agentes do arquivo YAML
agents_config_path = Path(__file__).parent / 'config/agents.yaml'
with open(agents_config_path, 'r', encoding='utf-8') as file:
    agents_config = yaml.safe_load(file)

# Inicializar ferramentas (singleton ou conforme necessidade)
# É importante configurar as API Keys e outros parâmetros via variáveis de ambiente (no .env)
# Ex: SERPER_API_KEY, LLAMACLOUD_API_KEY, SUPABASE_URL, etc.

# Ferramenta de busca web
serper_tool = SerperDevTool()
# llama_cloud_parser = LlamaParseDirectTool() # Comentada/Removida

# Ferramenta de consulta à Knowledge Base
# As configurações (Supabase URL, Key, Table Name, Embedding Model) são carregadas de variáveis de ambiente dentro da ferramenta
kb_tool = KnowledgeBaseQueryTool()
supabase_doc_tool = SupabaseDocumentContentTool() # Nova ferramenta


class CadastroAgents:
    """
    Classe para criar e configurar os agentes do "Crew de Cadastro".
    As definições base (role, goal, backstory) são carregadas do agents.yaml.
    As ferramentas são atribuídas aqui.
    """

    def triagem_validador_agente(self) -> Agent:
        config = agents_config['triagem_agente']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            tools=[
                supabase_doc_tool, # Para ler os documentos da tabela Supabase
                kb_tool
            ],
            # llm=seu_llm_configurado # Opcional: se quiser um LLM específico para este agente
        )

    def extrator_info_agente(self) -> Agent:
        config = agents_config['extrator_agente']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            tools=[
                supabase_doc_tool # Para ler os documentos da tabela Supabase
            ],
            # llm=seu_llm_configurado
        )

    def analista_risco_agente(self) -> Agent:
        config = agents_config['risco_agente']
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            tools=[
                supabase_doc_tool, # Para reler/confirmar dados da tabela Supabase
                serper_tool,        # Para busca web
                kb_tool             # Para consultar histórico, padrões de fraude, políticas
            ],
            # llm=seu_llm_configurado
        )

# Exemplo de como você poderia usar esta classe em seu crew.py:
# from .agents import CadastroAgents
# agents_manager = CadastroAgents()
# agente_triagem = agents_manager.triagem_validador_agente()
# agente_extrator = agents_manager.extrator_info_agente()
# agente_risco = agents_manager.analista_risco_agente() 