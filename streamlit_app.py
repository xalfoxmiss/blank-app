import streamlit as st
import requests
import base64
import json

# --- CONFIGURACIÓN ---
API_KEY = "rdlns_sk_20c632c13c914c0a1e4d92f03d88663c112a019c3719bbc3"
API_URL = "https://api.ruedalens.com/v1/analyze"
BASE_SEARCH_URL = "https://pre.muchoneumatico.com/neumaticos/buscar"

# --- FUNCIONES ---

def encode_image(image_file):
    """
    Codifica la imagen a Base64 asegurando que leemos desde el principio.
    CRÍTICO: st.image() mueve el puntero al final, seek(0) lo devuelve al inicio.
    """
    if image_file is not None:
        image_file.seek(0)  # <--- ESTA ES LA SOLUCIÓN AL ERROR
        return base64.b64encode(image_file.read()).decode('utf-8')
    return None

def extract_specs(vehicle_data):
    """
    Busca medidas válidas (ancho, perfil, llanta) priorizando:
    1. Lectura visual del neumático (current_tire)
    2. Ficha técnica delantera (oe_front_tire)
    3. Ficha técnica trasera (oe_rear_tire)
    """
    sources = [
        vehicle_data.get("current_tire", {}), 
        vehicle_data.get("oe_front_tire", {}),
        vehicle_data.get("oe_rear_tire", {})
    ]
    
    for tire in sources:
        # Validamos que tire no sea None y tenga los 3 datos
        if tire and tire.get("width") and tire.get("aspect_ratio") and tire.get("diameter"):
            return {
                "w": tire.get("width"),
                "ar": tire.get("aspect_ratio"),
                "d": tire.get("diameter")
            }
    return None

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

st.set_page_config(page_title="Ruedalens Scanner", page_icon="🚗", layout="centered")
st.title("🚗 Escáner de Neumáticos")
st.markdown("Sube las fotos para identificar el vehículo y buscar neumáticos compatibles.")

with st.form("main_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        tire_file = st.file_uploader("1. Foto Neumático (Primer plano)", type=['jpg', 'jpeg', 'png'])
        if tire_file:
            st.image(tire_file, caption="Vista Previa: Neumático", use_column_width=True)

    with col2:
        car_file = st.file_uploader("2. Foto Vehículo (Completo)", type=['jpg', 'jpeg', 'png'])
        if car_file:
            st.image(car_file, caption="Vista Previa: Vehículo", use_column_width=True)
    
    submitted = st.form_submit_button("🔍 ANALIZAR IMÁGENES", type="primary")

# --- LÓGICA DE EJECUCIÓN ---

if submitted:
    if not tire_file or not car_file:
        st.warning("⚠️ Por favor, sube ambas fotos antes de analizar.")
    else:
        with st.spinner("Procesando imágenes con IA..."):
            try:
                # 1. Codificar imágenes (incluye el fix del puntero)
                b64_tire = encode_image(tire_file)
                b64_car = encode_image(car_file)
                
                # 2. Preparar petición
                payload = {
                    "tireImage": b64_tire,
                    "carImage": b64_car
                }
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }

                # 3. Llamada a la API
                response = requests.post(API_URL, headers=headers, json=payload)
                result = response.json()
                
                # 4. Procesar Resultados
                # Extraemos la lista de vehículos de forma segura
                vehicles = result.get("data", {}).get("vehicles", [])
                
                # Validamos si hay al menos un vehículo y no es un objeto vacío {}
                has_valid_vehicle = False
                if vehicles and len(vehicles) > 0:
                    if vehicles[0].keys(): # Verifica que el diccionario tenga claves
                        has_valid_vehicle = True

                if result.get("success") and has_valid_vehicle:
                    vehicle = vehicles[0]
                    specs = extract_specs(vehicle)
                    
                    if specs:
                        # Datos encontrados
                        w, ar, d = specs['w'], specs['ar'], specs['d']
                        final_url = f"{BASE_SEARCH_URL}/{w}/{ar}/{d}/"
                        
                        st.success(f"✅ Identificado: {vehicle.get('brand')} {vehicle.get('model')}")
                        st.info(f"📏 Medida detectada: **{w}/{ar} R{d}**")
                        
                        # --- BOTÓN DE LLAMADA A LA ACCIÓN ---
                        st.markdown(f"""
                        <a href="{final_url}" target="_blank" style="text-decoration:none;">
                            <div style="
                                background-color: #FF5722;
                                color: white;
                                padding: 16px;
                                margin-top: 10px;
                                border-radius: 8px;
                                text-align: center;
                                font-weight: bold;
                                font-size: 20px;
                                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                                transition: 0.3s;
                            ">
                                🛒 VER PRECIOS Y COMPRAR ({w}/{ar} R{d})
                            </div>
                        </a>
                        <div style="text-align:center; font-size:12px; color:#888; margin-top:5px;">
                            {final_url}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.warning("⚠️ Se identificó el vehículo, pero la IA no pudo leer la medida completa del neumático.")
                        st.write("Intenta con una foto del flanco del neumático más clara.")
                
                elif result.get("success") and not has_valid_vehicle:
                    st.error("⚠️ La API respondió correctamente, pero no encontró ningún vehículo en las fotos.")
                    st.write("Asegúrate de que la foto del coche muestre el vehículo completo y la del neumático sea legible.")
                
                else:
                    st.error(f"❌ Error en la API: {result.get('error', 'Desconocido')}")

                # 5. Caja Colapsable de Debug (Requisito)
                st.divider()
                with st.expander("🛠️ Ver Respuesta Técnica Completa (JSON)"):
                    st.json(result)

            except Exception as e:
                st.error(f"💥 Error crítico de aplicación: {str(e)}")
