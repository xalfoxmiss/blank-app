import streamlit as st
import requests
import base64
import json

st.set_page_config(page_title="RuedaLens - Análisis de Neumáticos", layout="centered")

st.title("🔍 RuedaLens - Detección de Medida")

with st.form("image_upload_form"):
    st.subheader("Sube las imágenes")
    
    tire_image = st.file_uploader("Foto del neumático", type=['jpg', 'jpeg', 'png'])
    car_image = st.file_uploader("Foto del vehículo", type=['jpg', 'jpeg', 'png'])
    
    submit = st.form_submit_button("Analizar", type="primary", use_container_width=True)

if submit:
    if not tire_image or not car_image:
        st.error("Debes subir ambas imágenes")
    else:
        with st.spinner("Analizando imágenes..."):
            # Encode images to base64
            tire_b64 = base64.b64encode(tire_image.read()).decode()
            car_b64 = base64.b64encode(car_image.read()).decode()
            
            # API call
            try:
                response = requests.post(
                    'https://api.ruedalens.com/v1/analyze',
                    headers={
                        'Authorization': 'Bearer rdlns_sk_20c632c13c914c0a1e4d92f03d88663c112a019c3719bbc3',
                        'Content-Type': 'application/json',
                    },
                    json={
                        'tireImage': tire_b64,
                        'carImage': car_b64
                    },
                    timeout=30
                )
                
                result = response.json()
                
                if result.get('success') and result.get('data', {}).get('vehicles'):
                    vehicle = result['data']['vehicles'][0]
                    
                    # Extract tire dimensions
                    current_tire = vehicle.get('current_tire') or vehicle.get('oe_front_tire')
                    
                    if current_tire:
                        width = current_tire.get('width')
                        aspect = current_tire.get('aspect_ratio')
                        diameter = current_tire.get('diameter')
                        
                        if width and aspect and diameter:
                            # Build URL
                            search_url = f"https://pre.muchoneumatico.com/neumaticos/buscar/{width}/{aspect}/{diameter}/"
                            
                            st.success("✅ Análisis completado")
                            
                            st.subheader("🔗 Resultado")
                            st.markdown(f"### [{width}/{aspect} R{diameter}]({search_url})")
                            st.markdown(f"**[Ver neumáticos disponibles →]({search_url})**", unsafe_allow_html=True)
                            
                            # Collapsible full response
                            with st.expander("📋 Ver respuesta completa"):
                                st.json(result)
                        else:
                            st.warning("No se pudo extraer la medida completa")
                            with st.expander("Ver respuesta"):
                                st.json(result)
                    else:
                        st.warning("No se encontró información de neumático")
                        with st.expander("Ver respuesta"):
                            st.json(result)
                else:
                    st.error("No se detectó ningún vehículo válido")
                    with st.expander("Ver respuesta"):
                        st.json(result)
                        
            except requests.exceptions.Timeout:
                st.error("⏱️ Timeout - La API tardó demasiado")
            except requests.exceptions.RequestException as e:
                st.error(f"Error en la petición: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
