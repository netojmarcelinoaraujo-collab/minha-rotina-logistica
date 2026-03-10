import streamlit as st
import pandas as pd
import datetime
import os

# ==========================================
# 1. CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="Minha Rotina | Torre de Rotas", layout="wide")
COR_KAIZEN = "#00C3C3"

st.markdown(f"# 🎯 Meu Checklist Diário | <span style='color:{COR_KAIZEN};'>Torre de Controle</span>", unsafe_allow_html=True)

ARQUIVO_CSV = "minha_rotina_limpa.csv"

# ==========================================
# 2. DEFINIÇÃO DA SUA ROTINA PADRÃO
# ==========================================
ROTINA_PADRAO = {
    "🗺️ Rotas": [
        "Exportação dos dados", 
        "Verificação no grupo do whatsapp", 
        "Verificar Slowdown", 
        "Enviar report nos grupos"
    ],
    "📦 Coletas": [
        "Exportação dos dados", 
        "Passar dados a limpo", 
        "Validar analise"
    ],
    "📸 Canhotos": [
        "Validar canhotos", 
        "Passar dados a limpo", 
        "Enviar report"
    ],
    "📊 Quantidade de Rotas": [
        "Exportação dos dados", 
        "Passar dados a limpo"
    ],
    "📡 Validação ao vivo": [
        "Acompanhamento em tempo real das Rotas"
    ]
}

# ==========================================
# 3. MOTOR DE DADOS (CORRIGIDO PARA DATAS)
# ==========================================
def inicializar_dados():
    if not os.path.exists(ARQUIVO_CSV):
        # Aqui ele já gera como objeto Data
        hoje = datetime.date.today()
        linhas = []
        for categoria, tarefas in ROTINA_PADRAO.items():
            for tarefa in tarefas:
                linhas.append({
                    "Data": hoje,
                    "Categoria": categoria,
                    "Tarefa": tarefa,
                    "Concluído": False
                })
        df = pd.DataFrame(linhas)
        df.to_csv(ARQUIVO_CSV, index=False)
        return df
    else:
        df = pd.read_csv(ARQUIVO_CSV)
        # O SEGREDO ESTÁ AQUI: Converter texto para Data real antes de ir para a tela
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df

df_rotina = inicializar_dados()

# ==========================================
# 4. PAINEL DE CONTROLE (FILTROS E PROGRESSO)
# ==========================================
datas_disponiveis = sorted(df_rotina["Data"].unique(), reverse=True)
data_selecionada = st.selectbox("📅 Selecione o dia para visualizar/editar:", datas_disponiveis)

df_dia = df_rotina[df_rotina["Data"] == data_selecionada].copy()

total_tarefas = len(df_dia)
tarefas_concluidas = df_dia["Concluído"].sum()
progresso = int((tarefas_concluidas / total_tarefas) * 100) if total_tarefas > 0 else 0

st.write(f"**Progresso do Dia:** {progresso}% concluído ({tarefas_concluidas} de {total_tarefas} tarefas)")
st.progress(progresso / 100)
st.write("") 

# ==========================================
# 5. EDITOR DE DADOS (A TABELA MÁGICA)
# ==========================================
st.markdown("### 📋 Lista de Tarefas")
st.info("Clique nas caixinhas da coluna 'Concluído ✅' para marcar o que já foi feito. Você também pode alterar os nomes se precisar!")

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

# ==========================================
# 6. BOTÃO DE SALVAMENTO
# ==========================================
st.write("")
if st.button("💾 Guardar Progresso", type="primary", use_container_width=True):
    df_rotina.update(df_editado)
    
    novas_linhas = df_editado[~df_editado.index.isin(df_dia.index)]
    if not novas_linhas.empty:
        df_rotina = pd.concat([df_rotina, novas_linhas], ignore_index=True)
        
    df_rotina.to_csv(ARQUIVO_CSV, index=False)
    st.success("Progresso salvo com sucesso!")
    st.rerun()

# ==========================================
# BÔNUS: BOTÃO PARA GERAR UM NOVO DIA
# ==========================================
st.divider()
with st.expander("⚙️ Gerenciar Dias"):
    st.write("Criar a lista de tarefas padrão para um novo dia:")
    novo_dia = st.date_input("Escolha a data:")
    if st.button("➕ Gerar Tarefas para esta Data"):
        if novo_dia in df_rotina["Data"].values:
            st.warning("Já existem tarefas criadas para este dia!")
        else:
            linhas_novo_dia = []
            for categoria, tarefas in ROTINA_PADRAO.items():
                for tarefa in tarefas:
                    linhas_novo_dia.append({
                        "Data": novo_dia, # Adicionando como data real
                        "Categoria": categoria,
                        "Tarefa": tarefa,
                        "Concluído": False
                    })
            df_novo = pd.DataFrame(linhas_novo_dia)
            df_atualizado = pd.concat([df_rotina, df_novo], ignore_index=True)
            df_atualizado.to_csv(ARQUIVO_CSV, index=False)
            st.success(f"Rotina criada para {novo_dia.strftime('%d/%m/%Y')}! Atualize a página.")
            st.rerun()