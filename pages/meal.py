import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
from datetime import datetime
import zipfile
from matplotlib.backends.backend_pdf import PdfPages

# Carregar os dados da tabela
caminho_csv = 'C:/Users/ricar/OneDrive/Documentos/nutriçãoStreamlit/data/taco.csv'
tabela_taco = pd.read_csv(caminho_csv, on_bad_lines='skip')

# Função para gerar e baixar CSV
def to_csv(df, data):
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()

# Função para gerar e baixar Excel
def to_excel(df, data):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Resultados')
    buffer.seek(0)
    return buffer.getvalue()

# Função para gerar e retornar o gráfico como uma imagem em bytes
def get_plot_image(fig):
    img_bytes = BytesIO()
    fig.savefig(img_bytes, format='png')
    img_bytes.seek(0)
    return img_bytes

# Função para gerar e retornar um arquivo ZIP contendo imagens dos gráficos
def create_zip_with_plots_and_csv(figs_and_titles, csv_data, nome_csv):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for fig, title in figs_and_titles:
            img_bytes = get_plot_image(fig)
            zip_file.writestr(f'{title}.png', img_bytes.getvalue())
        zip_file.writestr(f'{nome_csv}.csv', csv_data)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

# Função para gerar um arquivo PDF com todas as imagens dos gráficos
def create_pdf_with_plots(figs_and_titles):
    pdf_buffer = BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        for fig, title in figs_and_titles:
            pdf.savefig(fig)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# Função principal da aplicação
def main():
    st.title("Selecionador de Alimentos")

    # Selecionar alimentos diretamente no campo multiselect
    opcoes = tabela_taco['Nome'].unique()

    # Inicializar a lista de alimentos selecionados e o estado da tabela confirmada na sessão, se não existir
    if 'alimentos_selecionados' not in st.session_state:
        st.session_state.alimentos_selecionados = []
        st.session_state.tabela_confirmada = False
        st.session_state.referencias_armazenadas = []  # Lista para armazenar referências de refeições

    # Campo multiselect para selecionar os alimentos
    novos_selecionados = st.multiselect(
        "Selecione os alimentos:",
        opcoes,
        default=st.session_state.alimentos_selecionados
    )

    # Campo para armazenar a data associada aos alimentos
    data_selecionada = st.date_input("Selecione a data:")

    # Botão para exibir os alimentos selecionados
    if st.button("Exibir Seleção de Alimentos"):
        st.session_state.alimentos_selecionados = novos_selecionados
        st.session_state.tabela_confirmada = True

    # Botão para salvar as refeições selecionadas
    if st.button("Salvar Refeições"):
        # Armazenar a seleção atual na lista de referências armazenadas
        refeicao = {
            'data': data_selecionada,
            'alimentos': novos_selecionados
        }
        st.session_state.referencias_armazenadas.append(refeicao)
        st.write("Refeição salva com sucesso!")

    # Botão para iniciar uma nova refeição
    if st.button("Limpar Lista de Alimentos"):
        # Resetar o estado da sessão para limpar a seleção anterior
        st.session_state.alimentos_selecionados = []
        st.session_state.tabela_confirmada = False
        st.rerun()  # Recarregar a página para refletir a nova seleção

    # Exibir a tabela filtrada e gráficos somente se a seleção for confirmada
    if st.session_state.tabela_confirmada:
        # Filtrar a tabela com base nos alimentos selecionados
        tabela_filtrada = tabela_taco[tabela_taco['Nome'].isin(st.session_state.alimentos_selecionados)]

        # Selecionar explicitamente as colunas desejadas
        colunas_desejadas = ['Nome', 'Energia (kcal)', 'Proteína (g)', 'Lipídeos (g)', 'Colesterol (mg)', 'Carboidrato (g)', 'Fibra Alimentar (g)']
        tabela_filtrada = tabela_filtrada[colunas_desejadas]

        # Converter as colunas para valores numéricos e preencher NaNs com 0
        for coluna in colunas_desejadas[1:]:  # Ignora a coluna 'Nome'
            tabela_filtrada[coluna] = pd.to_numeric(tabela_filtrada[coluna], errors='coerce').fillna(0)

        # Filtrar alimentos que têm todos os valores de nutrientes iguais a 0
        tabela_filtrada = tabela_filtrada[(tabela_filtrada[colunas_desejadas[1:]] > 0).any(axis=1)]

        # Calcular a soma dos nutrientes
        soma_nutrientes = tabela_filtrada.drop(columns='Nome').sum()

        # Exibir a tabela filtrada
        st.write("Tabela de nutrientes dos alimentos selecionados:")
        st.dataframe(tabela_filtrada)

        # Criar o gráfico de barras horizontais empilhadas
        fig_bar, ax_bar = plt.subplots(figsize=(10, 7))
        tabela_filtrada.set_index('Nome')[colunas_desejadas[1:]].plot(kind='barh', stacked=True, ax=ax_bar)
        ax_bar.set_title("Total de Nutrientes por Alimento")
        ax_bar.set_xlabel("Quantidade")
        ax_bar.set_ylabel("Alimento")
        ax_bar.legend(title="Nutrientes")
        st.pyplot(fig_bar)

        # Criar gráficos circulares para cada nutriente e armazenar em uma lista
        figs_and_titles = []
        for coluna in colunas_desejadas[1:]:  # Ignora a coluna 'Nome'
            dados = tabela_filtrada[['Nome', coluna]]
            dados = dados[dados[coluna] > 0]  # Filtrar valores iguais a 0
            dados_grouped = dados.groupby('Nome').sum()  # Agrupar por nome do alimento e somar os nutrientes

            # Verificar se há dados para plotar
            if not dados_grouped.empty:
                fig_pie, ax_pie = plt.subplots()
                ax_pie.pie(dados_grouped[coluna], labels=dados_grouped.index, autopct='%1.1f%%', startangle=90)
                ax_pie.set_title(f"{coluna} (Total: {soma_nutrientes[coluna]:.2f})")
                figs_and_titles.append((fig_pie, f"grafico_pizza_{coluna}"))
                
                # Exibir o gráfico
                st.pyplot(fig_pie)
                
                # Exibir o total geral
                st.write(f"Total geral para {coluna}: {soma_nutrientes[coluna]:.2f}")
            else:
                st.write(f"Gráfico de {coluna}:")
                st.write("Sem Dados")

        # Adicionar botões para download
        nome_arquivo = f"dados_refeicao_{data_selecionada.strftime('%Y-%m-%d')}"
        
        csv = to_csv(tabela_filtrada, nome_arquivo)
        st.download_button(
            label="Baixar Tabela como CSV",
            data=csv,
            file_name=f'{nome_arquivo}.csv',
            mime='text/csv'
        )

        excel = to_excel(tabela_filtrada, nome_arquivo)
        st.download_button(
            label="Baixar Tabela como Excel",
            data=excel,
            file_name=f'{nome_arquivo}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Adicionar botão para baixar todos os gráficos em um arquivo PDF
        pdf_file = create_pdf_with_plots(figs_and_titles)
        st.download_button(
            label="Baixar Todos os Gráficos em PDF",
            data=pdf_file,
            file_name=f'{nome_arquivo}_graficos.pdf',
            mime='application/pdf'
        )

        # Adicionar botão para baixar todos os gráficos
        zip_file = create_zip_with_plots_and_csv(figs_and_titles, csv, nome_arquivo)
        st.download_button(
            label="Baixar Todos os Gráficos e Tabela como ZIP",
            data=zip_file,
            file_name=f'{nome_arquivo}_graficos_e_csv.zip',
            mime='application/zip'
        )

if __name__ == "__main__":
    main()
