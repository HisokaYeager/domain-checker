import streamlit as st
import requests
import concurrent.futures
import re
from bs4 import BeautifulSoup

# --- Preparation dyal l'page ---
st.set_page_config(page_title="Domains Redirect Checker", page_icon="🔍", layout="centered")

TARGET_TEXT = "404 Sorry! That page cannot be found… The URL was either incorrect, you took a wrong guess or there is a technical problem"

def normalize_text(text):
    return re.sub(r'\s+', ' ', text).strip().lower()

TARGET_TEXT_NORMALIZED = normalize_text(TARGET_TEXT)

def check_single_domain(domain):
    url = domain if domain.startswith("http") else f"http://{domain}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text_clean = normalize_text(soup.get_text())

        if TARGET_TEXT_NORMALIZED in page_text_clean:
            return domain
    except requests.RequestException:
        pass
    return None

# --- L'interface Web (UI) ---
st.title("🔍 Domains Redirect Checker")
st.markdown("Paste your domains below.")

raw_domains = st.text_area("📝 Enter Domains (One per line):", height=200, placeholder="example.com\ntest.org")

if st.button("▶ Start Scan", type="primary"):
    if not raw_domains.strip():
        st.warning("⚠️ Please enter at least one domain to scan.")
    else:
        domains = list(set([d.strip() for d in raw_domains.split('\n') if d.strip()]))
        total_domains = len(domains)
        valid_domains = []
        
        progress_text = f"Scanning {total_domains} unique domains..."
        my_bar = st.progress(0, text=progress_text)
        completed = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_domain = {executor.submit(check_single_domain, domain): domain for domain in domains}
            for future in concurrent.futures.as_completed(future_to_domain):
                valid_domain = future.result()
                completed += 1
                progress_percentage = completed / total_domains
                my_bar.progress(progress_percentage, text=f"Scanning... {completed}/{total_domains} done.")
                if valid_domain:
                    valid_domains.append(valid_domain)
        
        my_bar.empty() 
        
        if valid_domains:
            st.success(f"✅ Scan complete! Found {len(valid_domains)} matching domains.")
            result_text = "\n".join(valid_domains)
            st.code(result_text, language="text")
            
            st.download_button(
                label="💾 Download Results (TXT)",
                data=result_text,
                file_name="clean_working_domains.txt",
                mime="text/plain"
            )
        else:
            st.error("❌ Scan complete! No domains matched the target 404 error.")
