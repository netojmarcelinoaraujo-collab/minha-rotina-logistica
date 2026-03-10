import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Minha Rotina | Torre de Rotas", layout="wide")
COR_KAIZEN = "#00C3C3"

st.markdown(f"# 🎯 Meu Checklist Diário | <span style='color:{COR_KAIZEN};'>Nuvem Ativada ☁️</span>", unsafe_allow_html=True)

# Botão de segurança para destravar a memória em caso de erros na nuvem
if st.button("🔄 Atualizar Conexão / Limpar Cache", type="secondary"):
    st.cache_data.clear()
    st.rerun()

conn = st.connection("gsheets", type=GSheetsConnection)

ROTINA_PADRAO = {
    "🗺️ Rotas": ["Exportação dos dados", "Verificação no grupo do whatsapp", "Verificar Slowdown", "Enviar report nos grupos"],
    "📦 Coletas": ["Exportação dos dados", "Passar dados a limpo", "Validar analise"],
    "📸 Canhotos": ["Validar canhotos", "Passar dados a limpo", "Enviar report"],
    "📊 Quantidade de Rotas": ["Exportação dos dados", "Passar dados a limpo"],
    "📡 Validação ao vivo": ["Acompanhamento em tempo real das Rotas"]
}

try:
    df_rotina = conn.read(worksheet="Página1", ttl=2)
except Exception as e:
    st.error("A Google bloqueou o acesso temporariamente. Aguarde uns minutos e clique em Atualizar Conexão.")
    st.stop()

if df_rotina.empty or "Data" not in df_rotina.columns:
    st.warning("A inicializar a base de dados na nuvem pela primeira vez...")
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    linhas = []
    for categoria, tarefas in ROTINA_PADRAO.items():
        for tarefa in tarefas:
            linhas.append({"Data": hoje, "Categoria": categoria, "Tarefa": tarefa, "Concluído": False})
    
    df_novo = pd.DataFrame(linhas)
    
    try:
        conn.update(worksheet="Página1", data=df_novo)
        st.cache_data.clear()
        st.success("✅ Base criada! Por favor, clique no botão 'Atualizar Conexão' lá em cima.")
    except Exception as e:
        st.error(f"Erro ao criar a base inicial. Detalhes: {e}")
    st.stop()

# ==========================================
# O GRANDE FILTRO DE LIMPEZA (Blindagem)
# ==========================================
# 1. Remove linhas completamente vazias que o Google Sheets manda por engano
df_rotina = df_rotina.dropna(how='all')

# 2. Força a conversão da 'Data' (valores inválidos são ignorados)
df_rotina['Data'] = pd.to_datetime(df_rotina['Data'], errors='coerce').dt.date

# 3. Força a coluna 'Concluído' a ser Verdadeiro ou Falso de verdade
if 'Concluído' in df_rotina.columns:
    df_rotina['Concluído'] = df_rotina['Concluído'].apply(lambda x: str(x).strip().upper() == 'TRUE')

# 4. Remove qualquer linha fantasma onde a Data não existia
df_rotina = df_rotina.dropna(subset=['Data'])
# ==========================================

datas_disponiveis = sorted(df_rotina["Data"].unique(), reverse=True)

if not datas_disponiveis:
    st.info("Nenhuma rotina válida encontrada na planilha. Limpe a planilha no Google e recarregue.")
    st.stop()

data_selecionada = st.selectbox("📅 Selecione o dia para visualizar/editar:", datas_disponiveis)

df_dia = df_rotina[df_rotina["Data"] == data_selecionada].copy()

total_tarefas = len(df_dia)
tarefas_concluidas = df_dia["Concluído"].sum()
progresso = int((tarefas_concluidas / total_tarefas) * 100) if total_tarefas > 0 else 0

st.write(f"**Progresso do Dia:** {progresso}% concluído")
st.progress(progresso / 100)
st.write("")

st.markdown("### 📋 Lista de Tarefas (Sincronizada ao Vivo)")
df_editado = st.data_editor(
    df_dia,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",
    column_config={
        "Data": st.column_config.DateColumn("Data", format="YYYY-MM-DD"),
        "Categoria": st.column_config.SelectboxColumn("Categoria", options=list(ROTINA_PADRAO.keys())),
        "Tarefa": st.column_config.TextColumn("Tarefa"),
        "Concluído": st.column_config.CheckboxColumn("Concluído ✅", default=False)
    }
)

if st.button("☁️ Sincronizar Progresso com o Google", type="primary", use_container_width=True):
    df_rotina.update(df_editado)
    
    novas_linhas = df_editado[~df_editado.index.isin(df_dia.index)]
    if not novas_linhas.empty:
        df_rotina = pd.concat([df_rotina, novas_linhas], ignore_index=True)
        
    with st.spinner('A guardar na nuvem...'):
        try:
            # Converte a data de volta para texto antes de mandar para o Google
            df_salvar = df_rotina.copy()
            df_salvar['Data'] = df_salvar['Data'].astype(str)
            conn.update(worksheet="Página1", data=df_salvar)
            st.cache_data.clear()
            st.success("Sincronizado! O Google Sheets foi atualizado com a equipa.")
        except Exception as e:
            st.error(f"Erro de sincronização: {e}")

st.divider()
with st.expander("⚙️ Gerenciar Dias"):
    novo_dia = st.date_input("Escolha a data:")
    if st.button("➕ Gerar Tarefas para esta Data"):
        if novo_dia in df_rotina["Data"].values:
            st.warning("Já existem tarefas criadas para este dia!")
        else:
            linhas_novo_dia = []
            for categoria, tarefas in ROTINA_PADRAO.items():
                for tarefa in tarefas:
                    linhas_novo_dia.append({"Data": novo_dia, "Categoria": categoria, "Tarefa": tarefa, "Concluído": False})
            df_novo = pd.DataFrame(linhas_novo_dia)
            df_atualizado = pd.concat([df_rotina, df_novo], ignore_index=True)
            
            try:
                df_atualizado['Data'] = df_atualizado['Data'].astype(str)
                conn.update(worksheet="Página1", data=df_atualizado)
                st.cache_data.clear()
                st.success(f"Rotina criada para {novo_dia.strftime('%d/%m/%Y')}! Atualize a página.")
            except Exception as e:
                st.error("Erro ao gerar novo dia.")
