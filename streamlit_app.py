
import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io
import json
import time

# OpenAI API Config
API_KEY = "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"
API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #000000; font-family: 'Helvetica Neue', sans-serif; color: #ffffff; }
    .main-container { background-color: transparent; padding: 20px; max-width: 900px; margin: 20px auto; }
    h1 { color: #ffffff; font-size: 32px; text-align: center; font-weight: 700; margin-bottom: 20px; }
    h3 { color: #ffffff; font-size: 22px; margin-top: 20px; font-weight: 600; }
    .stTextInput, .stTextArea, .stFileUploader { background-color: #1a1a1a; border: none; border-radius: 8px; padding: 12px; color: #ffffff; box-shadow: 0 0 10px #00ffff, 0 0 20px #00ffff; margin-bottom: 20px; transition: box-shadow 0.3s ease; }
    .stTextArea { box-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff; }
    .stFileUploader { box-shadow: 0 0 10px #8000ff, 0 0 20px #8000ff; }
    .stTextInput:focus, .stTextArea:focus { box-shadow: 0 0 15px #ffffff, 0 0 25px #ffffff; }
    .stButton>button { background: linear-gradient(90deg, #00ffff, #ff00ff); color: #ffffff; border: none; border-radius: 8px; padding: 12px 25px; font-weight: bold; box-shadow: 0 0 10px #00ffff; transition: transform 0.2s ease, box-shadow 0.2s ease; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 0 15px #ff00ff; }
    .output-text { background-color: #1a1a1a; padding: 15px; border-radius: 8px; border-left: 5px solid #00ffff; color: #ffffff; margin-top: 15px; line-height: 1.5; }
    </style>
""", unsafe_allow_html=True)

# Extraction Functions
def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = ' '.join(p.get_text() for p in soup.find_all('p'))
        return text
    except Exception as e:
        return f"Error fetching URL: {e}"

def process_text(text):
    return text.strip()

def extract_text_from_image(image_file):
    return "Image OCR not implemented yet. Please use text or URL input."

# OpenAI API Call with Optional Debugging
def analyze_with_openai(content, debug=False):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = (
        "Analyze the following text for political bias. Determine if it is left-leaning, right-leaning, or neutral. "
        "Quote directly from the text to support your analysis. Provide a detailed breakdown including tone, framing, "
        "language, and assumptions, plus additional insights like emotional appeal or intended audience. Format your "
        "response with these exact section headers: Bias Assessment, Direct Quotes, Detailed Analysis, Additional Findings, Summary.\n\n"
        f"Text:\n{content}"
    )
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a political bias analysis expert. Use the exact section headers requested."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }
    
    if debug:
        st.write(f"DEBUG: Sending request with payload: {json.dumps(payload, indent=2)[:200]}...")
    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=10)
        if debug:
            st.write(f"DEBUG: Status Code: {response.status_code}")
            st.write(f"DEBUG: Response: {response.text[:300]}...")
        response.raise_for_status()
        result = response.json()
        
        if "choices" not in result or not result["choices"]:
            if debug:
                st.error("DEBUG: No choices in response. API returned empty result.")
            return {"Bias Assessment": "Error: Empty API response", "Direct Quotes": "N/A", "Detailed Analysis": "N/A", "Additional Findings": "N/A", "Summary": "N/A"}
        
        analysis = result["choices"][0]["message"]["content"].strip()
        if debug:
            st.write(f"DEBUG: Raw Analysis: {analysis}")

        # Robust parsing
        sections = {
            "Bias Assessment": "",
            "Direct Quotes": "",
            "Detailed Analysis": "",
            "Additional Findings": "",
            "Summary": ""
        }
        current_section = None
        lines = analysis.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            for section in sections:
                if line.lower().startswith(section.lower()):
                    current_section = section
                    sections[current_section] = line[len(section):].strip() + "\n"
                    if debug:
                        st.write(f"DEBUG: Found section '{section}' starting with: {line}")
                    break
            else:
                if current_section and line:
                    sections[current_section] += line + "\n"

        if not any(sections.values()):
            if debug:
                st.write("DEBUG: No sections detected. Using raw analysis.")
            sections["Summary"] = f"Raw API Output:\n{analysis}"
        
        for section in sections:
            sections[section] = sections[section].strip()
            if not sections[section]:
                sections[section] = f"No {section.lower()} provided by API."

        return sections
    except requests.exceptions.HTTPError as e:
        if debug:
            st.error(f"API Error: {e}")
        return {"Bias Assessment": f"API Error: {e}", "Direct Quotes": "N/A", "Detailed Analysis": "N/A", "Additional Findings": "N/A", "Summary": "N/A"}
    except Exception as e:
        if debug:
            st.error(f"General Error: {e}")
        return {"Bias Assessment": f"Error: {e}", "Direct Quotes": "N/A", "Detailed Analysis": "N/A", "Additional Findings": "N/A", "Summary": "N/A"}

# Streamlit App
st.markdown('<div class="main-container">', unsafe_allow_html=True)
st.title("Political Bias Detector")
st.write("Dive into websites, text, or photos to uncover political bias with precision.")

# Debug Toggle
debug_mode = st.checkbox("Show debug info", value=False)

# Website URL Section
st.text_input("Enter URL:", placeholder="https://example.com", key="url")
if st.button("Analyze URL"):
    url = st.session_state.url
    if url:
        with st.spinner("Extracting and analyzing..."):
            content = extract_text_from_url(url)
            st.markdown(f'<div class="output-text">Extracted content: {content[:500] + "..." if len(content) > 500 else content}</div>', unsafe_allow_html=True)
            result = analyze_with_openai(content, debug=debug_mode)
            st.subheader("Bias Assessment")
            st.markdown(f'<div class="output-text">{result["Bias Assessment"]}</div>', unsafe_allow_html=True)
            st.subheader("Direct Quotes")
            st.markdown(f'<div class="output-text">{result["Direct Quotes"]}</div>', unsafe_allow_html=True)
            st.subheader("Detailed Analysis")
            st.markdown(f'<div class="output-text">{result["Detailed Analysis"]}</div>', unsafe_allow_html=True)
            st.subheader("Additional Findings")
            st.markdown(f'<div class="output-text">{result["Additional Findings"]}</div>', unsafe_allow_html=True)
            st.subheader("Summary")
            st.markdown(f'<div class="output-text">{result["Summary"]}</div>', unsafe_allow_html=True)

# Text Section
st.text_area("Enter text:", height=150, placeholder="Paste your text here...", key="text")
if st.button("Analyze Text"):
    text = st.session_state.text
    if text:
        with st.spinner("Analyzing..."):
            content = process_text(text)
            result = analyze_with_openai(content, debug=debug_mode)
            st.subheader("Bias Assessment")
            st.markdown(f'<div class="output-text">{result["Bias Assessment"]}</div>', unsafe_allow_html=True)
            st.subheader("Direct Quotes")
            st.markdown(f'<div class="output-text">{result["Direct Quotes"]}</div>', unsafe_allow_html=True)
            st.subheader("Detailed Analysis")
            st.markdown(f'<div class="output-text">{result["Detailed Analysis"]}</div>', unsafe_allow_html=True)
            st.subheader("Additional Findings")
            st.markdown(f'<div class="output-text">{result["Additional Findings"]}</div>', unsafe_allow_html=True)
            st.subheader("Summary")
            st.markdown(f'<div class="output-text">{result["Summary"]}</div>', unsafe_allow_html=True)

# Photo Section
st.file_uploader("Upload a photo:", type=["jpg", "png"], key="photo")
if st.button("Analyze Photo"):
    photo = st.session_state.photo
    if photo:
        with st.spinner("Processing..."):
            content = extract_text_from_image(photo)
            st.markdown(f'<div class="output-text">Extracted content: {content}</div>', unsafe_allow_html=True)
            result = analyze_with_openai(content, debug=debug_mode)
            st.subheader("Bias Assessment")
            st.markdown(f'<div class="output-text">{result["Bias Assessment"]}</div>', unsafe_allow_html=True)
            st.subheader("Direct Quotes")
            st.markdown(f'<div class="output-text">{result["Direct Quotes"]}</div>', unsafe_allow_html=True)
            st.subheader("Detailed Analysis")
            st.markdown(f'<div class="output-text">{result["Detailed Analysis"]}</div>', unsafe_allow_html=True)
            st.subheader("Additional Findings")
            st.markdown(f'<div class="output-text">{result["Additional Findings"]}</div>', unsafe_allow_html=True)
            st.subheader("Summary")
            st.markdown(f'<div class="output-text">{result["Summary"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
