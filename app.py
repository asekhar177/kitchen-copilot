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
JSON_FILE = "user_recipes.json"

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
    
    # Start with our base defaults or loaded file
    recipes_to_sort = default_recipes
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r") as f:
                recipes_to_sort = json.load(f)
        except:
            recipes_to_sort = default_recipes

    # 1. Anchor the Custom option at the very top
    ordered_recipes = {"Custom / Obscure Dish...": ""}
    
    # 2. Extract, sort the remaining keys alphabetically, and append them
    sorted_keys = sorted([k for k in recipes_to_sort.keys() if k != "Custom / Obscure Dish..."])
    for key in sorted_keys:
        ordered_recipes[key] = recipes_to_sort[key]
        
    return ordered_recipes

def save_recipes(recipes):
    """Saves the recipe dictionary to the local JSON storage file."""
    with open(JSON_FILE, "w") as f:
        json.dump(recipes, f, indent=4)

# Load current state of the recipe bank into local memory
if "recipe_bank" not in st.session_state:
    st.session_state.recipe_bank = load_recipes()

st.set_page_config(page_title="The Multimodal Sous Chef", page_icon="👩‍🍳", layout="centered")
st.title("👩‍🍳 The Multimodal Sous Chef")
st.write("Smart pocket sous chef with live on-screen saving capabilities. Developed by Arjun Sekhar, a culinary rookie.")

# --- SIDEBAR: RECIPE SAVER & SELECTOR ---
st.sidebar.header("📁 Recipe Memory Vault")

# Dropdown to choose existing recipes
selected_recipe = st.sidebar.selectbox("Choose a recipe:", list(st.session_state.recipe_bank.keys()))

st.sidebar.markdown("---")
st.sidebar.subheader("💾 Save a New Recipe")
new_title = st.sidebar.text_input("Recipe Name:", placeholder="e.g., Creamy Garlic Prawns")
new_steps = st.sidebar.text_area("Steps / Instructions:", placeholder="1. Sauté garlic in butter...\n2. Add prawns...")

if st.sidebar.button("Save to Memory Bank"):
    if new_title and new_steps:
        st.session_state.recipe_bank[new_title] = new_steps
        save_recipes(st.session_state.recipe_bank)
        st.sidebar.success(f"'{new_title}' successfully saved!")
        st.rerun()  # Refresh app to update the dropdown instantly
    else:
        st.sidebar.error("Please fill out both the Name and Steps to save!")

# --- TEMPORARY RESET BUTTON ---
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Cache & Reset Defaults"):
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
    if "recipe_bank" in st.session_state:
        del st.session_state.recipe_bank
    st.sidebar.success("Cache cleared! Reloading defaults...")
    st.rerun()

# Set default text area content based on dropdown selection
default_text = st.session_state.recipe_bank[selected_recipe]

# --- MAIN INTERFACE ---
uploaded_image = st.file_uploader("Step 1: Upload your cooking photo", type=["jpg", "jpeg", "png"])
recipe_text = st.text_area("Step 2: Active Recipe Instructions", value=default_text, height=180, 
                           placeholder="Type, paste, or select your recipe guidelines above...")

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
