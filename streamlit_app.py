import streamlit as st
import requests
import base64
import json

# --- Configuración ---
API_KEY = "rdlns_sk_20c632c13c914c0a1e4d92f03d88663c112a019c3719bbc3"
API_URL = "https://api.ruedalens.com/v1/analyze"
REDIRECT_BASE_URL = "https://pre.muchoneumatico.com/neumaticos/buscar"

# --- Funciones ---
def encode_image(image_file):
    """Codifica la imagen subida a Base64 string para la API."""
    if image_file is not None:
        return base64.b64encode(image_file.getvalue()).decode('utf-8')
    return None

def analyze_images(tire_b64, car_b64):
    """Envía las imágenes a la API de Ruedalens."""
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'tireImage': tire_b64,
        'carImage': car_b64
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status() # Lanza excepción para errores 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Ruedalens Quick Scan", page_icon="🚗")

st.title("🚗 Ruedalens Tire Scanner")
st.markdown("Sube una foto del **neumático** (lectura de flanco) y una del **coche**.")

# Formulario
with st.form("upload_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        tire_file = st.file_uploader("1. Foto Neumático", type=['jpg', 'jpeg', 'png'])
        if tire_file:
            st.image(tire_file, caption="Preview Neumático", use_column_width=True)

    with col2:
        car_file = st.file_uploader("2. Foto Vehículo", type=['jpg', 'jpeg', 'png'])
        if car_file:
            st.image(car_file, caption="Preview Vehículo", use_column_width=True)

    submitted = st.form_submit_button("🔍 Analizar y Buscar")

# Lógica principal
if submitted:
    if not tire_file or not car_file:
        st.error("⚠️ Faltan datos: Por favor sube ambas imágenes.")
    else:
        with st.spinner("Procesando imágenes en Ruedalens API..."):
            # 1. Preparar Payload
            tire_b64 = encode_image(tire_file)
            car_b64 = encode_image(car_file)
            
            # 2. Llamada API
            result = analyze_images(tire_b64, car_b64)

            # 3. Procesar Respuesta
            if "error" in result:
                st.error(f"Error de conexión: {result['error']}")
            elif result.get("success"):
                st.success("✅ Vehículo identificado")
                
                try:
                    # Extracción segura de datos
                    # Asumimos que el primer vehículo es el correcto
                    vehicle = result["data"]["vehicles"][0]
                    
                    # Intentamos sacar datos del neumático actual, sino del OE (Original Equipment)
                    tire_data = vehicle.get("current_tire") or vehicle.get("oe_front_tire")
                    
                    if tire_data:
                        w = tire_data.get("width")
                        ar = tire_data.get("aspect_ratio")
                        d = tire_data.get("diameter")

                        if w and ar and d:
                            # Construcción de URL final
                            target_url = f"{REDIRECT_BASE_URL}/{w}/{ar}/{d}/"
                            
                            st.divider()
                            st.subheader("Resultados")
                            
                            # Mostrar medida detectada
                            st.info(f"Medida detectada: **{w}/{ar} R{d}** | Vehículo: {vehicle.get('brand')} {vehicle.get('model')}")
                            
                            # Botón/Link Principal
                            st.markdown(f"""
                            <a href="{target_url}" target="_blank" style="text-decoration:none;">
                                <div style="
                                    background-color: #FF5722; 
                                    color: white; 
                                    padding: 16px; 
                                    border-radius: 8px; 
                                    text-align: center; 
                                    font-weight: bold; 
                                    font-size: 20px; 
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                    🛒 VER PRECIOS EN MUCHONEUMATICO ({w}/{ar} R{d})
                                </div>
                            </a>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning("La API detectó el coche pero no pudo leer las dimensiones completas del neumático.")
                    else:
                        st.warning("No se encontraron datos de neumáticos en la respuesta.")

                except Exception as e:
                    st.error(f"Error parseando la respuesta: {e}")

                # 4. Debug Data (Colapsable)
                st.divider()
                with st.expander("🛠️ Ver JSON de respuesta completo (Copiar)"):
                    st.code(json.dumps(result, indent=2), language="json")
            else:
                st.error("La API devolvió success: false")
                st.json(result)
