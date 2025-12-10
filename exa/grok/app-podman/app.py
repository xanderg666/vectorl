#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import time
import json
from datetime import datetime
import uuid
import os
from typing import List, Dict, Any
from grok_assistant import GrokOCIAssistant

# Configuración de página
st.set_page_config(
    page_title="Grok-4 Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# INICIALIZACIÓN DEL SESSION STATE
# ============================================================================
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'grok_assistant' not in st.session_state:
    try:
        st.session_state.grok_assistant = GrokOCIAssistant()
    except Exception as e:
        st.error(f"Error inicializando Grok Assistant: {e}")
        st.stop()

# CSS estilo Dracula
st.markdown("""
<style>
    .main { 
        background-color: #282a36;
        color: #f8f8f2;
    }

    .stApp {
        background-color: #282a36;
        color: #f8f8f2;
    }

    .user-message {
        background: #44475a;
        color: #f8f8f2;
        font-weight: 400;
        border-radius: 12px 12px 2px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 80%;
        float: right;
        clear: both;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        border-left: 3px solid #6272a4;
    }

    .assistant-message {
        background: #373844;
        color: #f8f8f2;
        font-weight: 400;
        border-radius: 12px 12px 12px 2px;
        padding: 12px 16px;
        margin: 8px 0;
        max-width: 80%;
        float: left;
        clear: both;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        border-left: 3px solid #8be9fd;
    }

    .message-time {
        font-size: 0.75em;
        opacity: 0.7;
        margin-top: 4px;
        font-weight: normal;
    }

    .stButton>button {
        border-radius: 8px;
        border: 1px solid #6272a4;
        background: linear-gradient(45deg, #44475a, #6272a4);
        color: #f8f8f2;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(45deg, #6272a4, #8be9fd);
        color: #282a36;
    }

    .file-badge {
        display: inline-block;
        background: #50fa7b;
        color: #282a36;
        padding: 4px 8px;
        border-radius: 4px;
        margin: 2px;
        font-size: 0.85em;
        font-weight: bold;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #44475a;
    }

    /* Text inputs */
    .stTextInput>div>div>input {
        background-color: #44475a;
        color: #f8f8f2;
        border: 1px solid #6272a4;
    }

    /* Text areas */
    .stTextArea>div>div>textarea {
        background-color: #44475a;
        color: #f8f8f2;
        border: 1px solid #6272a4;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def process_uploaded_file(uploaded_file) -> str:
    """Guarda archivo subido temporalmente y retorna la ruta"""
    try:
        # Crear directorio temporal si no existe
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Guardar archivo
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    except Exception as e:
        st.error(f"Error procesando archivo: {e}")
        return None


def main():
    # Header
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <h1>🤖 Grok-4 Chat Assistant</h1>
        <p style='color: #8be9fd;'>Powered by Oracle Cloud Infrastructure</p>
    </div>
    """, unsafe_allow_html=True)

    # Layout principal
    sidebar, chat_area = st.columns([1, 3])

    with sidebar:
        st.subheader("⚙️ Configuración")
        
        # Información del modelo
        st.info("**Modelo:** Grok-4\n\n**Max Tokens:** 20,000\n\n**Temperature:** 1.0")
        
        st.markdown("---")
        
        # System Prompt personalizado
        st.subheader("🎯 System Prompt")
        use_custom_prompt = st.checkbox(
            "Usar System Prompt personalizado",
            help="Define instrucciones específicas para el comportamiento del AI"
        )
        
        custom_prompt = ""
        if use_custom_prompt:
            custom_prompt = st.text_area(
                "System Prompt:",
                height=100,
                placeholder="Ej: Eres un experto en programación Python. Responde de manera concisa y técnica...",
                help="Define el comportamiento y personalidad del asistente"
            )
            if custom_prompt:
                st.caption(f"📝 Caracteres: {len(custom_prompt)}")
        
        st.markdown("---")
        
        # Subida de archivos
        st.subheader("📄 Archivos")
        uploaded_files = st.file_uploader(
            "Subir archivos",
            type=["txt", "pdf", "json", "md", "jpg", "jpeg", "png", "bmp", "gif", "webp"],
            accept_multiple_files=True,
            help="Sube imágenes, PDFs o archivos de texto para hacer preguntas sobre ellos"
        )
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} archivo(s) cargado(s):**")
            for file in uploaded_files:
                file_type = "📄" if file.type.startswith("text") or file.name.endswith((".md", ".json")) else "🖼️" if file.type.startswith("image") else "📕"
                st.write(f"{file_type} {file.name}")
        
        st.markdown("---")
        
        # Información de sesión
        st.subheader("📊 Información")
        st.write(f"**Mensajes:** {len(st.session_state.messages)}")
        st.write(f"**Conversación ID:**")
        st.caption(st.session_state.conversation_id[:8])
        
        st.markdown("---")
        
        # Limpiar conversación
        if st.button("🗑️ Nueva conversación", type="secondary"):
            st.session_state.messages = []
            st.session_state.conversation_id = str(uuid.uuid4())
            st.session_state.uploaded_files = []
            st.rerun()
        
        # Exportar conversación
        if st.session_state.messages:
            st.markdown("---")
            if st.button("💾 Exportar Chat"):
                export_data = {
                    'conversation_id': st.session_state.conversation_id,
                    'timestamp': datetime.now().isoformat(),
                    'messages': st.session_state.messages
                }
                st.download_button(
                    label="📥 Descargar JSON",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False),
                    file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    with chat_area:
        # Mostrar mensajes
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                        <div class="user-message">
                            {msg['content']}
                            <div class="message-time">{msg['timestamp']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    elapsed = f" • {msg.get('elapsed_time', '')}" if 'elapsed_time' in msg else ""
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                        <div class="assistant-message">
                            {msg['content'].replace('\n', '<br>')}
                            <div class="message-time">{msg['timestamp']}{elapsed}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Input de usuario
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                user_input = st.text_input(
                    "Escribe tu mensaje...",
                    placeholder="¿En qué puedo ayudarte?",
                    label_visibility="collapsed"
                )
            with col2:
                send_button = st.form_submit_button("Enviar", type="primary")

        # Procesar entrada
        if send_button and user_input.strip():
            start_time = time.time()

            # Agregar mensaje del usuario
            st.session_state.messages.append({
                'role': 'user',
                'content': user_input,
                'timestamp': datetime.now().strftime("%H:%M")
            })

            # Procesar archivos subidos
            file_paths = []
            if uploaded_files:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text(f"Procesando {len(uploaded_files)} archivo(s)...")
                for i, file in enumerate(uploaded_files):
                    file_path = process_uploaded_file(file)
                    if file_path:
                        file_paths.append(file_path)
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                progress_bar.empty()
                status_text.empty()

            # Generar respuesta
            with st.spinner("🤔 Generando respuesta con Grok-4..."):
                try:
                    response = st.session_state.grok_assistant.generate_response(
                        prompt=user_input,
                        model_name="grok-4",
                        system_prompt=custom_prompt if use_custom_prompt and custom_prompt else None,
                        files=file_paths if file_paths else None
                    )
                    
                    elapsed = f"{time.time() - start_time:.1f}s"
                    
                    # Agregar respuesta del asistente
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': response,
                        'timestamp': datetime.now().strftime("%H:%M"),
                        'elapsed_time': elapsed
                    })
                    
                except Exception as e:
                    st.error(f"Error generando respuesta: {e}")
                    st.session_state.messages.append({
                        'role': 'assistant',
                        'content': f"❌ Error: {str(e)}",
                        'timestamp': datetime.now().strftime("%H:%M")
                    })
            
            # Limpiar archivos temporales
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
            
            st.rerun()


if __name__ == "__main__":
    main()
