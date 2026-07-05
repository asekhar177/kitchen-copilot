import streamlit as st
from openai import OpenAI
import base64
import json
import os

# Initialize OpenAI Client securely
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def encode_image(uploaded_file):
    """Encodes an uploaded file into a base64 string."""
    return base64.b64encode(uploaded_file.read()).decode("utf-8")

# --- FILE PATH FOR MEMORY ---
JSON_FILE = "curachef_recipes.json"

def load_recipes():
    """Loads recipes from the JSON file or initializes defaults if it doesn't exist."""
    default_recipes = {
        "Custom / Obscure Dish...": "",
        "Classic Tomato Fusilli Pasta": (
            "1. Boil fusilli in salted water until al dente, then drain.\n"
            "2. In a separate pot, simmer tomato passata, garlic, and olive oil for 10 minutes.\n"
            "3. Add the drained fusilli directly into the sauce pot. Toss vigorously on low heat for 1-2 minutes until every spiral is evenly coated, glossy, and the sauce adheres nicely to the ridges.\n"
            "4. Garnish with fresh basil or grated parmesan and serve hot."
        ),
        "Citrus Marmalade": (
            "1. Simmer sliced citrus peel and pulp in water for 1.5 to 2 hours until tender and translucent.\n"
            "2. Add sugar and lemon juice over low heat; stir constantly until granules completely dissolve.\n"
            "3. Bring to a rapid, rolling boil on high heat. Watch for volatile, fast-popping foam.\n"
            "4. Continue boiling hard until foam subsides into a heavier, slower boil with large, glossy 'fish eye' bubbles.\n"
            "5. Test: Turn off heat. Drop onto chilled saucer. Push after 1 min; if it wrinkles, setting point (105°C) is reached.\n"
            "6. Rest 15 mins to settle peel evenly, then pour into sterile jars."
        )
    }
    
    recipes_to_sort = default_recipes
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                recipes_to_sort = json.load(f)
        except:
            recipes_to_sort = default_recipes

    ordered_recipes = {"Custom / Obscure Dish...": ""}
    sorted_keys = sorted([k for k in recipes_to_sort.keys() if k != "Custom / Obscure Dish..."])
    for key in sorted_keys:
        ordered_recipes[key] = recipes_to_sort[key]
        
    return ordered_recipes

def save_recipes(recipes):
    """Saves the recipe dictionary to the local JSON storage file."""
    with open(JSON_FILE, "w") as f:
        json.dump(recipes, f, indent=4)

if "recipe_bank" not in st.session_state:
    st.session_state.recipe_bank = load_recipes()

# --- BRANDED INTERFACE CONFIGURATION ---
st.set_page_config(page_title="CuraChef AI | Smart Pocket Sous Chef", page_icon="🍳", layout="centered")
st.title("🍳 CuraChef Studio")
st.write("The multimodal sous chef with real-time pan monitoring.")

# --- SIDEBAR: RECIPE SAVER & SELECTOR ---
st.sidebar.header("📁 Recipe Profiles")

selected_recipe = st.sidebar.selectbox("Choose a recipe profile:", list(st.session_state.recipe_bank.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("💾 Create a New Recipe Profile")
new_title = st.sidebar.text_input("Recipe Name:", placeholder="e.g., Creamy Garlic Prawns")
new_steps = st.sidebar.text_area("Analytical Steps:", placeholder="1. Sauté garlic...\n2. Track emulsion...")

if st.sidebar.button("Inspect My Pan"):
    if new_title and new_steps:
        st.session_state.recipe_bank[new_title] = new_steps
        save_recipes(st.session_state.recipe_bank)
        st.sidebar.success(f"'{new_title}' successfully committed!")
        st.rerun()
    else:
        st.sidebar.error("Please provide both a Name and Steps.")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reset Vault Defaults"):
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
    if "recipe_bank" in st.session_state:
        del st.session_state.recipe_bank
    st.sidebar.success("Vault wiped. Reloading factory defaults...")
    st.rerun()

default_text = st.session_state.recipe_bank[selected_recipe]

# --- MAIN INTERFACE ---
uploaded_image = st.file_uploader("Step 1: Capture live pan state (Photo)", type=["jpg", "jpeg", "png"])
recipe_text = st.text_area("Step 2: Target Recipe Execution Guidelines", value=default_text, height=180, 
                           placeholder="Awaiting target instructions...")

if st.button("Run Pan Analysis"):
    if not uploaded_image:
        st.error("Missing physical pan image data!")
    elif not recipe_text:
        st.error("Missing recipe guideline parameters!")
    else:
        with st.spinner("Processing visual data against recipe parameters..."):
            try:
                base64_image = encode_image(uploaded_image)
                
                system_prompt = (
                    "You are the CuraChef analytical system, an elite precision culinary agent. "
                    "Analyze physical cooking progress solely using the verified target guidelines provided.\n\n"
                    f"--- TARGET PARAMETERS ---\n{recipe_text}\n---------------------"
                )
                
                user_prompt = (
                    "Perform step-matching telemetry on this pan state.\n"
                    "Output exactly three concise evaluation fields:\n"
                    "1. CURRENT STATUS & RECIPE MATCH: (Identify current step alignment.)\n"
                    "2. VERDICT: (Must be exactly one: [UNDER-COOKED / KEEP SIMMERING], [PERFECT / MOVE TO NEXT STEP], or [DANGER / BURNING])\n"
                    "3. NEXT ACTION: (Prescribe immediate chemical or physical correction step.)"
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
                
                st.success("Telemetry complete!")
                st.markdown("### 📊 CuraChef System Diagnostics")
                st.write(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Analysis error: {e}")
