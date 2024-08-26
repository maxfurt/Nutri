import streamlit as st


home = st.Page("./pages/home.py", title="Home")
new_meal = st.Page("./pages/meal.py", title="Consuta de Nutrientes")
report = st.Page("./pages/report.py", title="Relatório")


navbar = st.navigation({
        "Controle de macronutrientes": [home, new_meal, report]
})

navbar.run()