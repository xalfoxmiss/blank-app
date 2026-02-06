import streamlit as st
import requests
import base64
import json

# --- Configuración ---
API_KEY = "rdlns_sk_20c632c13c914c0a1e4d92f03d88663c112a019c3719bbc3"
API_URL = "https://api.ruedalens.com/v1/analyze"
BASE_SEARCH_URL = "https://pre.muchoneumatico.com/neumaticos/buscar"

# --- Función de Codificación Robusta ---
def encode_image(image_file):
    if image_file is not None:
        # 1. IMPORTANTE: Reiniciar el puntero al inicio del archivo
        # Si Streamlit usó el archivo para la preview, el puntero está al final.
        image_file.seek(0)
        
        # 2. Leer bytes y codificar
        bytes_data = image_file.getvalue()
        b64_str = base64.b64encode(bytes_data).decode('utf-8')
        
        # 3. Debug: Imprimir tamaño para asegurar que no está vacío
        # st.write(f"Debug: Imagen codificada tamaño: {len(b64_str)} caracteres")
        return b64_str
    return None

def extract_specs(vehicle_data):
    # Prioridad: 1. Leído (current) -> 2. Ficha Técnica (oe_front) -> 3. Trasero (oe_rear)
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

# --- UI ---
st.set_page_config(page_title="Ruedalens App", page_icon="🚗")
st.title("🚗 Escáner de Neumáticos")

with st.form("main_form"):
    c1, c2 = st.columns(2)
    with c1:
        tire_file = st.file_uploader("1. Foto Neumático", type=['jpg', 'jpeg', 'png'])
        if tire_file: 
            st.image(tire_file, caption="Neumático")
    with c2:
        car_file = st.file_uploader("2. Foto Vehículo", type=['jpg', 'jpeg', 'png'])
        if car_file: 
            st.image(car_file, caption="Vehículo")
    
    submitted = st.form_submit_button("🔍 Analizar", type="primary")

if submitted:
    if not tire_file or not car_file:
        st.warning("⚠️ Sube ambas fotos.")
    else:
        with st.spinner("Procesando..."):
            try:
                # Codificación
                b64_tire = encode_image(tire_file)
                b64_car = encode_image(car_file)
                
                # Verificación de seguridad (Debug)
                if len(b64_tire) < 100 or len(b64_car) < 100:
                    st.error("❌ Error: Las imágenes parecen estar vacías al procesarlas. Intenta subirlas de nuevo.")
                    st.stop()

                # Payload
                payload = {
                    "tireImage": b64_tire,
                    "carImage": b64_car
                }
                
                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                }

                # Llamada
                response = requests.post(API_URL, headers=headers, json=payload)
                result = response.json()
                
                # --- Procesamiento ---
                vehicles = result.get("data", {}).get("vehicles", [])
                
                # Check si hay vehículos y no son objetos vacíos
                valid_vehicle = False
                if vehicles and len(vehicles) > 0:
                    # A veces devuelve [{}], verificamos que tenga claves dentro
                    if vehicles[0].keys():
                        valid_vehicle = True

                if result.get("success") and valid_vehicle:
                    vehicle = vehicles[0]
                    specs = extract_specs(vehicle)
                    
                    if specs:
                        w, ar, d = specs['w'], specs['ar'], specs['d']
                        url = f"{BASE_SEARCH_URL}/{w}/{ar}/{d}/"
                        
                        st.success(f"✅ Medida: {w}/{ar} R{d}")
                        st.markdown(f"**Coche:** {vehicle.get('brand')} {vehicle.get('model')}")
                        
                        st.markdown(f"""
                        <a href="{url}" target="_blank" style="text-decoration:none;">
                            <div style="background-color:#FF5722;color:white;padding:15px;border-radius:5px;text-align:center;font-weight:bold;font-size:18px;">
                                👉 VER PRECIOS Y COMPRAR
                            </div>
                        </a>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Se detectó el vehículo, pero no la medida exacta del neumático.")
                else:
                    st.error("⚠️ No se detectó ningún vehículo en las imágenes. Intenta con fotos más claras.")

                st.divider()
                with st.expander("Ver Respuesta Técnica (JSON)"):
                    st.json(result)

            except Exception as e:
                st.error(f"Error técnico: {e}")
