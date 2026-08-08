"""
Streamlit UI - takes a question, calls the FastAPI backend, shows the
answer with its sources and confidence/faithfulness so a user can see
not just the answer but how much to trust it.
"""

import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="MarketplaceIQ", page_icon="🛒")
st.title("MarketplaceIQ")
st.caption("Ask about Flipkart, Amazon India, or Meesho policies - returns, GST, shipping, disputes, and more")

question = st.text_input("Your question")

if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        try:
            response = requests.post(f"{BACKEND_URL}/ask", json={"question": question}, timeout=60)
            response.raise_for_status()
            result = response.json()

            st.write(result["answer"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Confidence", result["confidence"])
            col2.metric("Model used", result["model_used"])
            col3.metric("Judge verdict", "Faithful" if result["judge_faithful"] else "Flagged")

            if result["citations"]:
                st.caption("Sources: " + ", ".join(result["citations"]))

            if not result["guardrail_passed"]:
                st.warning("A citation in this answer could not be verified against the retrieved sources.")

        except requests.exceptions.RequestException as e:
            st.error(f"Couldn't reach the backend: {e}")
