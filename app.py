import streamlit as st
from openai import OpenAI
import base64

# Initialize the client securely using the Streamlit secrets vault name
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    """Encodes a Streamlit uploaded file into a base64 string."""
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

st.set_page_config(page_title="AI Kitchen Co-Pilot", page_icon="👩‍🍳")
st.title("👩‍🍳 Multi-Modal Kitchen Co-Pilot")
st.write("Upload a live photo of your pan and your recipe to get real-time feedback.")

# 1. UI Elements for Uploading Files
uploaded_image = st.file_uploader("Step 1: Upload your cooking photo", type=["jpg", "jpeg", "png"])
recipe_text = st.text_area("Step 2: Paste your recipe steps here", height=150, placeholder="1. Sauté onions...\n2. Add spices...")

# 2. Run Analysis when button is clicked
if st.button("Inspect My Pan"):
    if not uploaded_image:
        st.error("Please upload a photo of your pan first!")
    elif not recipe_text:
        st.error("Please add your recipe instructions!")
    else:
        with st.spinner("Chef is analyzing your dish... Please wait."):
            try:
                base64_image = encode_image(uploaded_image)
                
                system_prompt = (
                    "You are an expert Michelin-star sous chef. Your job is to analyze live kitchen photos "
                    f"and guide a cook based explicitly on the provided recipe guidelines.\n\n"
                    f"--- TARGET RECIPE ---\n{recipe_text}\n---------------------"
                )
                
                user_prompt = (
                    "Analyze this pan image in the context of the provided recipe.\n"
                    "Provide your analysis in exactly three short sections:\n"
                    "1. CURRENT STATUS & RECIPE MATCH: (Identify which step of the recipe the pan appears to be on.)\n"
                    "2. VERDICT: (Choose exactly one: [UNDER-COOKED / KEEP SIMMERING], [PERFECT / MOVE TO NEXT STEP], or [DANGER / BURNING])\n"
                    "3. NEXT ACTION: (State exactly what the cook needs to do next.)"
                )

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                        }
                    ],
                    max_tokens=350
                )
                
                st.success("Analysis Complete!")
                st.markdown("### 🍳 Chef's Feedback")
                st.write(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")