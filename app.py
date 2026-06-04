import streamlit as st
# Cambia esto: import google.generativeai as genai
from google import genai
from PIL import Image
import base64
import os
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="UTSFIT IA", page_icon="🍎", layout="wide")

# --- FUNCIÓN PARA APLICAR EL FONDO ---
def aplicar_estilo():
    background_code = ""
    if os.path.exists("fondo.jpeg"):
        with open("fondo.jpeg", "rb") as f:
            data = f.read()
            bin_str = base64.b64encode(data).decode()
        background_code = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        </style>
        """
    st.markdown(f"""
        {background_code}
        <style>
        h1 {{ color: #2e7d32 !important; background-color: rgba(255, 255, 255, 0.8); padding: 10px; border-radius: 10px; display: inline-block; }}
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:first-child {{ background-color: transparent !important; border: none !important; }}
        div.stButton > button {{ background-color: #ffffff !important; color: #000000 !important; border: 1px solid #000000 !important; width: 100%; }}
        div.stButton > button:hover {{ background-color: #000000 !important; color: #ffffff !important; }}
        [data-testid="stVerticalBlock"] > div:last-child {{ background-color: rgba(255, 255, 255, 0.95); padding: 2rem; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); color: #000000 !important; }}
        </style>
        """, unsafe_allow_html=True)

aplicar_estilo()

# --- MEMORIA DE NUTRIENTES (Session State) ---
if 'nutrientes' not in st.session_state:
    st.session_state.nutrientes = {'cal': 0, 'prot': 0, 'carb': 0, 'gras': 0}
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- BARRA LATERAL: CÁLCULOS FÍSICOS REALES ---
st.sidebar.title("👤 Perfil UTSFit")
peso = st.sidebar.number_input("Peso (kg)", 40.0, 150.0, 93.0)
altura = st.sidebar.number_input("Altura (cm)", 120, 220, 183)
edad = st.sidebar.number_input("Edad", 15, 80, 21)
objetivo = st.sidebar.selectbox("Tu Meta:", ["Déficit (Perder peso)", "Mantenimiento", "Volumen (Ganar músculo)"])

# Ecuación de Harris-Benedict
tmb = 66 + (13.7 * peso) + (5 * altura) - (6.8 * edad)
mantenimiento = tmb * 1.3  # Actividad ligera regular

if objetivo == "Déficit (Perder peso)":
    meta_cal = int(mantenimiento - 500)
elif objetivo == "Volumen (Ganar músculo)":
    meta_cal = int(mantenimiento + 500)
else:
    meta_cal = int(mantenimiento)

# Distribución inteligente de Macros (30% Proteína, 45% Carb, 25% Grasa)
meta_prot = int((meta_cal * 0.30) / 4)
meta_carb = int((meta_cal * 0.45) / 4)
meta_gras = int((meta_cal * 0.25) / 9)

st.sidebar.divider()
st.sidebar.write(f"🎯 **Meta Total:** {meta_cal} kcal")
st.sidebar.write(f"🥩 Prot: **{meta_prot}g** | 🍞 Carb: **{meta_carb}g** | 🥑 Gras: **{meta_gras}g**")

if st.sidebar.button("🗑️ Reiniciar Día"):
    st.session_state.nutrientes = {'cal': 0, 'prot': 0, 'carb': 0, 'gras': 0}
    st.session_state.historial = []
    st.rerun()

# --- CONEXIÓN CON GEMINI IA ---
GOOGLE_API_KEY = "AIzaSyA5us9JOGnPGbt2egMFYnbibuKwDScLOn8" 

# Inicializamos el cliente moderno de Google con la clave
client = genai.Client(api_key=GOOGLE_API_KEY)

def analizar_plato_ia(img):
    prompt = """Analiza la comida de la imagen. Da un resumen muy breve de los alimentos encontrados.
    Al final de tu respuesta, debes escribir OBLIGATORIAMENTE el siguiente formato numérico estricto:
    VALORES -> CAL: [num], PROT: [num], CARB: [num], GRAS: [num]"""
    
    # Llamada oficial usando el cliente moderno
    res = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[prompt, img]
    )
    return res.text

# --- ESTRUCTURA DE LA INTERFAZ ---
st.title("🍎 UTSFIT IA")

col_camara, col_resumen = st.columns([1.5, 1])

with col_camara:
    st.subheader("📸 Captura tu Comida")
    foto = st.camera_input("Enfoca tu plato")
    if foto:
        img = Image.open(foto)
        with st.spinner("La IA de la UTS está analizando tus macros..."):
            try:
                respuesta_ia = analizar_plato_ia(img)
                st.info(respuesta_ia)
                
                # Extraer los datos al final del texto usando expresiones regulares
                seccion_valores = respuesta_ia.split("VALORES ->")[-1]
                numeros = re.findall(r"(\d+)", seccion_valores)
                
                if len(numeros) >= 4:
                    st.session_state.nutrientes['cal'] += int(numeros[0])
                    st.session_state.nutrientes['prot'] += int(numeros[1])
                    st.session_state.nutrientes['carb'] += int(numeros[2])
                    st.session_state.nutrientes['gras'] += int(numeros[3])
                    st.session_state.historial.append(f"Plato: {numeros[0]}kcal | P: {numeros[1]}g | C: {numeros[2]}g | G: {numeros[3]}g")
                    st.success("¡Nutrientes sumados al día!")
            except Exception as e:
                st.error("Hubo un problema con la IA. Comprueba tu internet.")

with col_resumen:
    st.header("📊 Resumen del Día")
    
    # Progreso de Calorías
    st.write(f"🔥 **Calorías:** {st.session_state.nutrientes['cal']} / {meta_cal} kcal")
    st.progress(min(st.session_state.nutrientes['cal'] / meta_cal, 1.0))
    
    # Progreso de Proteínas
    st.write(f"🥩 **Proteínas:** {st.session_state.nutrientes['prot']}g / {meta_prot}g")
    st.progress(min(st.session_state.nutrientes['prot'] / meta_prot, 1.0))
    
    # Progreso de Carbohidratos
    st.write(f"🍞 **Carbohidratos:** {st.session_state.nutrientes['carb']}g / {meta_carb}g")
    st.progress(min(st.session_state.nutrientes['carb'] / meta_carb, 1.0))
    
    # Progreso de Grasas
    st.write(f"🥑 **Grasas:** {st.session_state.nutrientes['gras']}g / {meta_gras}g")
    st.progress(min(st.session_state.nutrientes['gras'] / meta_gras, 1.0))
    
    st.divider()
    st.markdown('<p style="color:black; font-weight:bold;">📋 Historial de hoy:</p>', unsafe_allow_html=True)
    if not st.session_state.historial:
        st.write("Aún no has escaneado ninguna comida hoy.")
    else:
        for item in st.session_state.historial:
            st.write(item)