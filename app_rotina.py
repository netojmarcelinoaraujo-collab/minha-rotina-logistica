import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Minha Rotina | Torre de Rotas", layout="wide")
COR_KAIZEN = "#00C3C3"

st.markdown(f"# 🎯 Meu Checklist Diário | <span style='color:{COR_KAIZEN};'>Nuvem Ativada ☁️</span>", unsafe_allow_html=True)

# 1. Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

ROTINA_PADRAO = {
    "🗺️ Rotas": ["Exportação dos dados", "Verificação no grupo do whatsapp", "Verificar Slowdown", "Enviar report nos grupos"],
    "📦 Coletas": ["Exportação dos dados", "Passar dados a limpo", "Validar analise"],
    "📸 Canhotos": ["Validar canhotos", "Passar dados a limpo", "Enviar report"],
    "📊 Quantidade de Rotas": ["Exportação dos dados", "Passar dados a limpo"],
    "📡 Validação ao vivo": ["Acompanhamento em tempo real das Rotas"]
}

# 2. Carregar Dados da Nuvem
try:
    df_rotina = conn.read(worksheet="Página1") # Pode ser "Sheet1" dependendo do idioma do seu Google
except Exception:
    df_rotina = pd.DataFrame()

# 3. Se a planilha estiver vazia, cria a estrutura inicial
if df_rotina.empty:
    st.warning("Inicializando a base de dados na nuvem pela primeira vez...")
    hoje = datetime.date.today().strftime("%Y-%m-%d")
    linhas = []
    for categoria, tarefas in ROTINA_PADRAO.items():
        for tarefa in tarefas:
            linhas.append({"Data": hoje, "Categoria": categoria, "Tarefa": tarefa, "Concluído": False})
    df_rotina = pd.DataFrame(linhas)
    
    # CORREÇÃO AQUI: Impedir que o Streamlit tente deletar células do Google
    conn.update(worksheet="Página1", data=df_rotina, resize=False)
    st.rerun()

# Converte data para o formato correto na tela
df_rotina['Data'] = pd.to_datetime(df_rotina['Data']).dt.date

# 4. Filtros
datas_disponiveis = sorted(df_rotina["Data"].unique(), reverse=True)
data_selecionada = st.selectbox("📅 Selecione o dia para visualizar/editar:", datas_disponiveis)

df_dia = df_rotina[df_rotina["Data"] == data_selecionada].copy()

total_tarefas = len(df_dia)
tarefas_concluidas = df_dia["Concluído"].sum()
progresso = int((tarefas_concluidas / total_tarefas) * 100) if total_tarefas > 0 else 0

st.write(f"**Progresso do Dia:** {progresso}% concluído")
st.progress(progresso / 100)
st.write("")

# 5. Editor de Dados
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

# 6. Botão de Salvar na Nuvem
st.write("")
if st.button("☁️ Sincronizar Progresso com o Google", type="primary", use_container_width=True):
    df_rotina.update(df_editado)
    
    novas_linhas = df_editado[~df_editado.index.isin(df_dia.index)]
    if not novas_linhas.empty:
        df_rotina = pd.concat([df_rotina, novas_linhas], ignore_index=True)
        
    with st.spinner('A guardar na nuvem...'):
        # CORREÇÃO AQUI TAMBÉM: resize=False
        conn.update(worksheet="Página1", data=df_rotina, resize=False)
        st.cache_data.clear()
        st.success("Sincronizado! O Google Sheets foi atualizado.")

# 7. Gerar Novo Dia
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
            
            # CORREÇÃO AQUI TAMBÉM: resize=False
            conn.update(worksheet="Página1", data=df_atualizado, resize=False)
            st.cache_data.clear()
            st.success(f"Rotina criada para {novo_dia.strftime('%d/%m/%Y')}!")
            st.rerun()
