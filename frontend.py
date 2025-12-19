import streamlit as st
import requests
import uuid

# Page config
st.set_page_config(page_title="Real Estate AI Assistant", page_icon="🏠", layout="wide")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Title and description
st.title("🏠 Real Estate AI Assistant")
st.markdown("**Multi-Agent System** | Property Search • Booking • FAQ (RAG)")

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    This AI assistant has **3 specialized agents**:
    
    🔍 **PropertyAgent**  
    Search for properties by city, price range
    
    📅 **BookingAgent**  
    Schedule property viewings
    
    💡 **FAQAgent**  
    Answer real estate questions using RAG
    
    ---
    
    **Examples to try:**
    - "find me properties in Los Angeles"
    - "what documents do I need to buy?"
    - "book luxury apartment for tomorrow 2pm"
    - "can I view the same property twice?"
    """)
    
    st.divider()
    
    # Session info
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    
    if st.button("🔄 Clear Conversation"):
        # Clear session on backend
        try:
            requests.delete(f"http://127.0.0.1:8000/session/{st.session_state.session_id}")
        except:
            pass
        # Reset frontend
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about properties, book a viewing, or ask questions..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Call the agent API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 Thinking...")
        
        try:
            response = requests.post(
                "http://127.0.0.1:8000/agent/chat",
                json={
                    "message": prompt,
                    "session_id": st.session_state.session_id
                },
                timeout=90  # Increased to 90 seconds
            )
            
            if response.status_code == 200:
                data = response.json()
                reply = data.get("response", "No response received")
                
                # Display the response
                message_placeholder.markdown(reply)
                
                # Add assistant message to chat
                st.session_state.messages.append({"role": "assistant", "content": reply})
            else:
                error_msg = f"❌ API Error: {response.status_code} - {response.text[:200]}"
                message_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
        except requests.exceptions.Timeout:
            error_msg = "⏱️ Request timed out after 90 seconds. Try:\n\n1. Refresh the page\n2. Use simpler questions\n3. Check if FastAPI is running (http://127.0.0.1:8000/health)"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.divider()
st.caption("🔧 Powered by AutoGen • OpenAI GPT-4o-mini • RAG with PostgreSQL • Phoenix Observability")
