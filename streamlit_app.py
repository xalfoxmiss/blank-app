import streamlit as st
import requests
import base64
import json

# --- Configuración ---
API_KEY = "rdlns_sk_20c632c13c914c0a1e4d92f03d88663c112a019c3719bbc3"
API_URL = "https://api.ruedalens.com/v1/analyze"
BASE_SEARCH_URL = "https://pre.muchoneumatico.com/neumaticos/buscar"

# --- Funciones ---
def encode_image(image_file):
    """Codifica la imagen a Base64 string raw (sin cabeceras data:image...)"""
    if image_file is not None:
        # getvalue() obtiene los bytes, b64encode codifica, decode pasa a string
        return base64.b64encode(image_file.getvalue()).decode('utf-8')
    return None

def get_tire_info(vehicle_data):
    """Intenta extraer ancho, perfil y diámetro de current_tire o oe_front_tire"""
    # 1. Intentar leer neumático detectado (current_tire)
    tire = vehicle_data.get("current_tire")
    
    # 2. Si es nulo o faltan datos, intentar con el original (oe_front_tire)
    if not tire or not all([tire.get("width"), tire.get("aspect_ratio"), tire.get("diameter")]):
        tire = vehicle_data.get("oe_front_tire")
    
    if tire:
        return {
            "w": tire.get("width"),
            "ar": tire.get("aspect_ratio"),
            "d": tire.get("diameter")
        }
    return None

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Ruedalens Scanner", page_icon="🛞", layout="centered")

st.title("🛞 Ruedalens -> MuchoNeumático")
st.info("Sube las fotos para obtener el enlace directo de compra.")

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        tire_file = st.file_uploader("1. Foto Neumático (Primer plano)", type=['jpg', 'jpeg', 'png'])
    with c2:
        car_file = st.file_uploader("2. Foto Vehículo (Completo)", type=['jpg', 'jpeg', 'png'])
    
    submitted = st.form_submit_button("Analizar Imágenes", type="primary")

if submitted and tire_file and car_file:
    with st.spinner("Enviando a API Ruedalens..."):
        try:
            # Preparar payload
            payload = {
                "tireImage": encode_image(tire_file),
                "carImage": encode_image(car_file)
            }
            
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            # Llamada
            response = requests.post(API_URL, headers=headers, json=payload)
            result = response.json()
            
            # --- Lógica de Extracción y Visualización ---
            
            extracted_data = None
            search_url = None
            
            # Validar si hay datos en 'vehicles'
            if result.get("success") and result.get("data", {}).get("vehicles"):
                vehicles_list = result["data"]["vehicles"]
                
                # Comprobar que la lista no esté vacía y el primer objeto no sea {}
                if len(vehicles_list) > 0 and vehicles_list[0]:
                    vehicle = vehicles_list[0]
                    extracted_data = get_tire_info(vehicle)
                    
                    if extracted_data and all(extracted_data.values()):
                        w = extracted_data['w']
                        ar = extracted_data['ar']
                        d = extracted_data['d']
                        
                        # Componer URL: https://.../buscar/255/45/19/
                        search_url = f"{BASE_SEARCH_URL}/{w}/{ar}/{d}/"
                        
                        st.success(f"✅ Medida detectada: {w}/{ar} R{d}")
                        
                        # ENLACE VISIBLE (Botón HTML)
                        st.markdown(f"""
                        <a href="{search_url}" target="_blank" style="text-decoration:none;">
                            <div style="
                                background-color: #28a745;
                                color: white;
                                padding: 15px;
                                margin: 10px 0;
                                text-align: center;
                                border-radius: 8px;
                                font-size: 18px;
                                font-weight: bold;
                                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                            ">
                                🔗 IR A RESULTADOS ({w}/{ar} R{d})
                            </div>
                        </a>
                        <div style="text-align:center; font-size:0.8em; color:gray;">
                            {search_url}
                        </div>
                        """, unsafe_allow_html=True)
                        
                    else:
                        st.warning("⚠️ Se detectó el coche, pero no la medida completa de los neumáticos.")
                else:
                    st.error("⚠️ La API respondió success:true, pero no encontró vehículos (objeto vacío).")
            else:
                st.error(f"❌ Error en la API o no se detectó nada.")

            # --- Caja Colapsable con Output Completo (Requisito) ---
            st.divider()
            with st.expander("📦 Ver Output JSON Completo (Debug)", expanded=False):
                st.json(result)

        except Exception as e:
            st.error(f"Error de ejecución: {str(e)}")

elif submitted:
    st.warning("Por favor sube ambas fotos.")
