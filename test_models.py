import streamlit as st
from google import genai

api_key = st.secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("--- AVAILABLE MODELS FOR YOUR KEY ---")
try:
    for m in client.models.list():
        print(m.name)
except Exception as e:
    print(f"Error fetching models: {e}")