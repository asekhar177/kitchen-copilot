import streamlit as st
from openai import OpenAI
import base64

# Initialize the client securely using the Streamlit secrets vault name
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    """Encodes a Streamlit uploaded file into a base64 string."""
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

st.set_page_config(page_title="AI Kitchen Copilot", page_icon="👩‍🍳", layout="centered")
st.title("👩‍🍳 Multi-Modal Kitchen Co-Pilot v2.0")
st.write("Your pocket sous-chef with built-in culinary memory.")

# --- VERSION 2.0: RECIPE MEMORY BANK ---
RECIPE_BANK = {
    "Aloo Tikki Chaat (Street-Style)": (
        "1. Mash or grate completely cooled boiled potatoes. Mix with cornstarch, cumin, chaat masala, and salt. Shape into patties.\n"
        "2. Heat 2 tbsp oil in a heavy pan over medium heat. Place tikkis down to shallow fry.\n"
        "3. Shallow fry until the bottom turns deeply golden-brown and crispy. Flip gently.\n"
        "4. Fry second side until matching crunchy texture. Press down slightly to maximize crispiness.\n"
        "5. Remove and layer with yogurt, tamarind chutney, green chutney, red onions, and sev."
    ),
    "Citrus Marmalade (Chemistry-Based)": (
        "1. Simmer sliced citrus peel and pulp in water for 1.5 to 2 hours until tender and translucent.\n"
        "2. Add sugar and lemon juice over low heat; stir constantly until granules completely dissolve.\n"
        "3. Bring to a rapid, rolling boil on high heat. Watch for volatile, fast-popping foam.\n"
        "4. Continue boiling hard until foam subsides into a heavier, slower boil with large, glossy 'fish eye' bubbles.\n"
        "5. Test: Turn off heat. Drop onto chilled saucer. Push after 1 min; if it wrinkles, setting point (105°C) is reached.\n"
        "6. Rest 15 mins to settle peel evenly, then pour into sterile jars."
    ),
    "Fresh Egg Pasta Dough": (
        "1. Mound flour, create a deep well in the center, and crack eggs directly inside.\n"
        "2. Whisk eggs gently with a fork without breaking the outer flour walls.\n"
        "3. Gradually drag flour into the center until a thick custard-like paste forms.\n"
        "4. Collapse walls and bring dough together into a rough, shaggy ball.\n"
        "5. Knead vigorously for 8-10 mins until completely smooth, silky, and elastic.\n"
        "6. Wrap tightly in plastic wrap and let rest at room temperature for 30 minutes to relax gluten.\n"
        "7. Roll thin via machine or rolling pin, then cut into shapes."
    ),
    "Custom / Obscure Dish...": ""
}

# --- SIDEBAR: RECIPE SELECTOR ---
st.sidebar.header("📁 Recipe Memory")
selected_recipe = st.sidebar.selectbox("Choose a memorized recipe:", list(RECIPE_BANK.keys()))

# If they select a pre-saved recipe, grab it from memory, otherwise keep it blank for custom typing
default_text = RECIPE_BANK[selected_recipe]

# --- MAIN INTERFACE ---
uploaded_image = st.file_uploader("Step 1: Upload your cooking photo", type=["jpg", "jpeg", "png"])

# The text box now dynamically changes based on what you click in the sidebar!
recipe_text = st.text_area("Step 2: Recipe Instructions", value=default_text, height=180, 
                           placeholder="Type or paste custom recipe guidelines here...")

# 2. Run Analysis when button is clicked
if st.button("Inspect My Pan"):
    if not uploaded_image:
        st.error("Please upload a photo of your pan first!")
    elif not recipe_text:
        st.error("Please add or select your recipe instructions!")
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
