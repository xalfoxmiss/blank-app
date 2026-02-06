import streamlit as st
import requests
import base64
import json

# --- Configuración ---
# API Key proporcionada
API_KEY = "rdlns_sk_20c632c13c914c0a1e4d92f03d88663c112a019c3719bbc3"
API_URL = "https://api.ruedalens.com/v1/analyze"
BASE_SEARCH_URL = "https://pre.muchoneumatico.com/neumaticos/buscar"

# --- Funciones ---
def encode_image(image_file):
    """Codifica imagen a Base64 estándar (utf-8 string)"""
    if image_file is not None:
        return base64.b64encode(image_file.getvalue()).decode('utf-8')
    return None

def extract_specs(vehicle_data):
    """Extrae w, ar, d priorizando current_tire, fallback a oe_front_tire"""
    # Estrategia de cascada para encontrar datos
    sources = [
        vehicle_data.get("current_tire", {}), 
        vehicle_data.get("oe_front_tire", {}),
        vehicle_data.get("oe_rear_tire", {})
    ]
    
    for tire in sources:
        if tire and tire.get("width") and tire.get("aspect_ratio") and tire.get("diameter"):
            return {
                "w": tire.get("width"),
                "ar": tire.get("aspect_ratio"),
                "d": tire.get("diameter")
            }
    return None

# --- UI Streamlit ---
st.set_page_config(page_title="Ruedalens Debugger", page_icon="🔧")
st.title("🔧 Ruedalens API Integrator")

# Formulario
with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        tire_file = st.file_uploader("1. Neumático", type=['jpg', 'png', 'jpeg'])
    with c2:
        car_file = st.file_uploader("2. Vehículo", type=['jpg', 'png', 'jpeg'])
    
    btn_run = st.form_submit_button("EJECUTAR ANÁLISIS", type="primary")

if btn_run and tire_file and car_file:
    with st.spinner("Consultando API..."):
        try:
            # 1. Request
            payload = {
                "tireImage": encode_image(tire_file),
                "carImage": encode_image(car_file)
            }
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(API_URL, headers=headers, json=payload)
            result = response.json()

            # 2. VISIBILIDAD INMEDIATA (Crítico para debug)
            st.subheader("📡 Respuesta API Cruda")
            with st.expander("Ver JSON Completo", expanded=False):
                st.json(result)

            # 3. Lógica de Negocio
            success = result.get("success", False)
            vehicles = result.get("data", {}).get("vehicles", [])

            # Validar que vehicles sea una lista y tenga contenido real (no [{}])
            has_vehicle_data = isinstance(vehicles, list) and len(vehicles) > 0 and vehicles[0].keys()

            if success and has_vehicle_data:
                vehicle = vehicles[0]
                specs = extract_specs(vehicle)
                
                if specs:
                    w, ar, d = specs['w'], specs['ar'], specs['d']
                    final_url = f"{BASE_SEARCH_URL}/{w}/{ar}/{d}/"
                    
                    st.success(f"✅ Detección Exitosa: {w}/{ar} R{d}")
                    st.markdown(f"**Vehículo:** {vehicle.get('brand', 'Desc')} {vehicle.get('model', '')}")
                    
                    # CTA
                    st.markdown(f"""
                    <br>
                    <a href="{final_url}" target="_blank" style="text-decoration:none;">
                        <div style="background-color:#E63946; color:white; padding:18px; border-radius:6px; text-align:center; font-weight:bold; font-size:18px;">
                            🛒 VER PRECIOS ({w}/{ar} R{d})
                        </div>
                    </a>
                    <div style="text-align:center; margin-top:5px; color:#666; font-size:12px; font-family:monospace;">
                        {final_url}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Vehículo detectado, pero faltan dimensiones (Ancho/Perfil/Llanta) en la respuesta.")
            
            elif success and not has_vehicle_data:
                st.error("⚠️ La API devolvió 'success: true' pero la lista de vehículos está vacía o es nula ({}). La IA no encontró coches en la foto.")
            
            else:
                st.error(f"❌ Error API: {result.get('error', 'Success = False')}")

        except Exception as e:
            st.error(f"💥 Error de Ejecución (Python): {e}")

elif btn_run:
    st.warning("Sube ambas fotos para continuar.")
