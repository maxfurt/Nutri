import streamlit as st



st.title("Nome teste")
st.write("O nome teste é parceiro de sua sáude, te auxiliando a rastrear os macronutrientes de suas refeições.")

st.page_link("pages/meal.py", label="Nova Refeição")
st.page_link("pages/report.py", label="Gerar Relatório")


