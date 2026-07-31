import streamlit as st
import urllib.request
import json
import re

# Page config
st.set_page_config(
    page_title="AI Email Workspace",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    /* Global styles and typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .title-gradient {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 50%, #6366f1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Mock Email Composer Layout */
    .email-mock-card {
        background-color: #111827 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2) !important;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    
    .email-mock-header {
        border-bottom: 1px solid #1f2937;
        padding-bottom: 14px;
        margin-bottom: 18px;
        font-size: 0.95rem;
        color: #9ca3af;
        line-height: 1.5;
    }
    
    .email-mock-label {
        color: #6366f1;
        font-weight: 600;
        margin-right: 8px;
    }
    
    .email-mock-body {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #f3f4f6 !important;
        white-space: pre-wrap;
    }

    /* Chat bubble system for refinements */
    .chat-bubble-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 14px;
        max-width: 80%;
        font-size: 0.95rem;
        line-height: 1.4;
    }
    
    .bubble-user {
        background-color: #4f46e5;
        color: #ffffff;
        align-self: flex-end;
        border-bottom-right-radius: 2px;
        box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);
    }
    
    .bubble-ai {
        background-color: #1f2937;
        color: #e5e7eb;
        align-self: flex-start;
        border-bottom-left-radius: 2px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .bubble-meta {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 4px;
        display: block;
        font-weight: 500;
    }

    /* Metrics Cards */
    .status-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    .status-online {
        background: rgba(16, 185, 129, 0.1);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .status-offline {
        background: rgba(239, 68, 68, 0.1);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    
    /* Hover effects for Streamlit elements */
    .stButton > button {
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Helper Functions -----------------

def call_gemini(api_key, system_prompt, user_content):
    """Call Google Gemini API via direct HTTP request."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"System Guidelines: {system_prompt}\n\nUser Request: {user_content}"}]
            }
        ]
    }
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        raise Exception(f"Gemini API execution failed: {e}")

def call_llm(system_prompt, user_content, messages_history=None):
    """Central function to invoke cloud Gemini API."""
    if not st.session_state.api_key.strip():
        st.error("Please enter a valid Gemini API Key in the sidebar.")
        st.stop()
    
    # Build prompt from history if refinement is active
    if messages_history:
        combined_prompt = ""
        for msg in messages_history:
            combined_prompt += f"{msg['role'].upper()}: {msg['content']}\n\n"
        combined_prompt += f"USER: {user_content}"
        return call_gemini(st.session_state.api_key, system_prompt, combined_prompt)
    else:
        return call_gemini(st.session_state.api_key, system_prompt, user_content)

def analyze_email_text(text):
    """Perform static text inspection on the generated email."""
    if not text:
        return {}
        
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    read_time = max(1, round(word_count / 200))
    
    sentences = max(1, text.count('.') + text.count('!') + text.count('?'))
    avg_sentence_len = word_count / sentences
    if avg_sentence_len < 9:
        grade = "5th Grade (Very Easy)"
    elif avg_sentence_len < 13:
        grade = "8th Grade (Standard)"
    elif avg_sentence_len < 17:
        grade = "High School (Balanced)"
    elif avg_sentence_len < 22:
        grade = "College Level (Sophisticated)"
    else:
        grade = "Graduate / Executive (Advanced)"
        
    lower_text = text.lower()
    warmth_words = ["please", "thank", "hope", "great", "best", "excited", "happy", "forward", "appreciate", "welcome", "dear", "sincerely", "regards"]
    prof_words = ["sincerely", "regards", "confirm", "proceed", "deliverable", "schedule", "attachment", "meeting", "formal", "request", "collaborate"]
    urgency_words = ["urgent", "asap", "immediate", "deadline", "soon", "critical", "important", "now", "today", "quickly", "action required"]
    
    warmth_count = sum(lower_text.count(w) for w in warmth_words)
    prof_count = sum(lower_text.count(w) for w in prof_words)
    urgency_count = sum(lower_text.count(w) for w in urgency_words)
    
    warmth_score = min(100, warmth_count * 12 + 30)
    prof_score = min(100, prof_count * 10 + 40)
    urgency_score = min(100, urgency_count * 15 + 10)
    
    spam_trigger_words = ["free", "guarantee", "click here", "buy now", "100%", "earn money", "make money", "winner", "cash", "no obligation"]
    detected_spam = [w for w in spam_trigger_words if w in lower_text]
    
    return {
        "word_count": word_count,
        "char_count": char_count,
        "read_time_min": read_time,
        "readability": grade,
        "warmth": warmth_score,
        "professionalism": prof_score,
        "urgency": urgency_score,
        "spam_triggers": detected_spam
    }

# ----------------- Session State Init -----------------

if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "email_draft" not in st.session_state:
    st.session_state.email_draft = ""
if "subject_lines" not in st.session_state:
    st.session_state.subject_lines = []
if "refinement_history" not in st.session_state:
    st.session_state.refinement_history = []
if "raw_notes" not in st.session_state:
    st.session_state.raw_notes = ""

# ----------------- Sidebar -----------------

st.sidebar.markdown("### 🖥️ Gemini Connection")
if st.session_state.api_key.strip():
    st.sidebar.markdown('<div class="status-badge status-online">● Gemini Active</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="status-badge status-offline">● API Key Required</div>', unsafe_allow_html=True)

st.sidebar.write("")

# API Key Input
st.session_state.api_key = st.sidebar.text_input(
    "Gemini API Key", 
    value=st.session_state.api_key, 
    type="password",
    help="Paste a free Gemini API Key from Google AI Studio."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ✉️ Formatting Controls")

# Tone & Length
tone_options = ["Professional", "Friendly", "Apologetic", "Direct", "Urgent", "Humorous", "Custom"]
selected_tone = st.sidebar.selectbox("Email Tone", tone_options)
if selected_tone == "Custom":
    custom_tone = st.sidebar.text_input("Describe your tone", "Sarcastic but polite")
    tone_str = custom_tone
else:
    tone_str = selected_tone

length_options = {
    "Concise (Short)": "short, under 100 words, direct, max 2 paragraphs",
    "Balanced (Medium)": "standard email length, polite, complete structure with proper layout",
    "Detailed (Long)": "comprehensive details, fully elaborates the points, clear section separations, thorough explanation"
}
selected_length = st.sidebar.select_slider("Email Length", options=list(length_options.keys()), value="Balanced (Medium)")
length_str = length_options[selected_length]

# Language
language_options = ["English", "Spanish", "French", "German", "Japanese", "Chinese", "Italian"]
selected_language = st.sidebar.selectbox("Draft Language", language_options)

# ----------------- Main UI -----------------

st.markdown("<h1>✉️ AI Email Workspace</h1>", unsafe_allow_html=True)
st.markdown("Draft, refine, and inspect high-converting professional emails using Google Gemini API.")

tabs = st.tabs(["🚀 Workspace", "📋 Templates Library", "📊 AI Inspector", "⚙️ System Status"])

# ----------------- Tab 1: Workspace -----------------
with tabs[0]:
    col1, col2 = st.columns([5, 6], gap="large")
    
    with col1:
        st.markdown("### 📝 Draft Inputs")
        
        # User input area
        user_notes = st.text_area(
            "Enter bullet points, rough sentences, or key objectives:",
            value=st.session_state.raw_notes,
            placeholder="e.g., Ask manager for salary review. Mention 5 years in AI engineering. Mention london market rates.",
            height=250,
            key="input_raw_notes"
        )
        st.session_state.raw_notes = user_notes
        
        btn_c1, btn_c2 = st.columns([2, 1])
        with btn_c1:
            generate_clicked = st.button("✨ Draft Email Now", use_container_width=True, type="primary")
        with btn_c2:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True)
            if clear_clicked:
                st.session_state.raw_notes = ""
                st.session_state.email_draft = ""
                st.session_state.subject_lines = []
                st.session_state.refinement_history = []
                st.rerun()

        # Handle Generation Process
        if generate_clicked:
            if not user_notes.strip():
                st.warning("⚠️ Enter some rough notes first.")
            elif not st.session_state.api_key.strip():
                st.warning("⚠️ Please configure your Gemini API Key in the sidebar to generate emails.")
            else:
                with st.spinner("Drafting your email..."):
                    sys_prompt = f"""
                    You are an expert executive communication assistant.
                    Your goal is to rewrite the user's rough notes into a polished, professional email.
                    
                    Strict Formatting Rules:
                    1. Use the selected Tone: '{tone_str}'.
                    2. Maintain the requested Length constraint: '{length_str}'.
                    3. Write the response in '{selected_language}'.
                    4. Output ONLY the email body itself.
                    5. Start with 'Subject: [Subject Line]' at the top, then a blank line, then the greeting, paragraphs, sign-off.
                    6. Do NOT include any explanations, preamble introductions, or remarks. Just return the structured email content.
                    """
                    
                    # Generate Email
                    raw_email = call_llm(sys_prompt, user_notes)
                    st.session_state.email_draft = raw_email
                    st.session_state.refinement_history = [
                        {"role": "assistant", "content": raw_email}
                    ]
                    
                    # Deduce alternate subject lines
                    subj_prompt = f"""
                    Generate exactly 3 alternate email subject lines for the following email body.
                    Tone: '{tone_str}'. Language: '{selected_language}'.
                    Output ONLY 3 bulleted lines, one per line. No introductions or other text.
                    """
                    try:
                        raw_subjects = call_llm(subj_prompt, raw_email)
                        lines = [l.strip("-*• ").strip() for l in raw_subjects.split("\n") if l.strip()]
                        st.session_state.subject_lines = lines[:3]
                    except Exception:
                        st.session_state.subject_lines = []
                    st.rerun()
                    
    with col2:
        st.markdown("### 📨 Output Preview")
        
        if st.session_state.email_draft:
            # Parse Subject and Body
            draft_text = st.session_state.email_draft
            lines = draft_text.split("\n")
            subject = "AI Generated Email"
            body = draft_text
            
            for i, line in enumerate(lines[:3]):
                if line.lower().startswith("subject:"):
                    subject = line.replace("Subject:", "").replace("subject:", "").strip()
                    body = "\n".join(lines[i+1:]).strip()
                    break
            
            # Render Mock Email Client
            st.markdown(f"""
            <div class="email-mock-card">
                <div class="email-mock-header">
                    <div><span class="email-mock-label">To:</span> <span style="color: #9ca3af;">recipient@domain.com</span></div>
                    <div><span class="email-mock-label">Subject:</span> <span style="color: #f3f4f6; font-weight: 500;">{subject}</span></div>
                </div>
                <div class="email-mock-body">{body}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Collapsible copy and edit box
            with st.expander("📋 Copy / Manually Edit Draft", expanded=False):
                editable_email = st.text_area(
                    "You can copy or manually adjust the text below:",
                    value=st.session_state.email_draft,
                    height=180,
                    key="editable_email_box"
                )
                
            # Alternative subjects
            if st.session_state.subject_lines:
                st.markdown("**💡 Alternative Subject Options:**")
                for sub in st.session_state.subject_lines:
                    st.code(sub, language="markdown")
            
            st.markdown("---")
            
            # Refinement Section
            st.markdown("### 💬 Refine with AI")
            
            # Show conversation logs as clean chat bubbles
            if len(st.session_state.refinement_history) > 1:
                st.markdown('<div class="chat-bubble-container">', unsafe_allow_html=True)
                for index, item in enumerate(st.session_state.refinement_history):
                    if item["role"] == "user":
                        st.markdown(f"""
                        <div class="chat-bubble bubble-user">
                            <span class="bubble-meta">You (Change Request)</span>
                            {item['content']}
                        </div>
                        """, unsafe_allow_html=True)
                    elif item["role"] == "assistant" and index > 0:
                        st.markdown(f"""
                        <div class="chat-bubble bubble-ai">
                            <span class="bubble-meta">AI (Updated Draft {index // 2})</span>
                            Draft updated below. Click 'Copy / Edit' above to view full text.
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            refinement_feedback = st.text_input(
                "Request revision (e.g., 'make the tone softer', 'add a deadline for Friday at 4pm')",
                placeholder="Type changes...",
                key="feedback_input_field"
            )
            
            if st.button("🔄 Apply Revision", use_container_width=True):
                if refinement_feedback.strip():
                    with st.spinner("Applying edits..."):
                        refinement_sys = f"""
                        You are a professional editor revising an email draft.
                        Implement the user's change request precisely.
                        Maintain the overall tone guidelines ('{tone_str}') and language ('{selected_language}').
                        Format: Output ONLY the revised full email (start with Subject: at top). No chat dialogue, no explanations.
                        """
                        
                        # Add user request to chat logs
                        st.session_state.refinement_history.append({"role": "user", "content": refinement_feedback})
                        
                        # Call LLM with full context
                        refined_email = call_llm(refinement_sys, refinement_feedback, st.session_state.refinement_history[:-1])
                        
                        st.session_state.email_draft = refined_email
                        st.session_state.refinement_history.append({"role": "assistant", "content": refined_email})
                        st.rerun()
        else:
            st.info("Your drafted email will display here. Enter your notes on the left and click 'Draft Email Now'.")

# ----------------- Tab 2: Templates -----------------
with tabs[1]:
    st.subheader("📋 Pre-Configured Outlines")
    st.write("Select a template category to load its points into the input text area. Head back to the Workspace to customize and generate!")
    
    templates = {
        "💼 Cold Outreach": {
            "title": "Cold Outreach",
            "notes": "Hi [Name],\n\nI noticed your company is looking to scale your engineering team.\n\nIntroduce our service: we provide top-tier vetted developers matching your stack.\n\nHighlight results: we helped clients reduce hiring time by 45%.\n\nCall to Action: Are you available for a brief 10-minute call next Tuesday at 2 PM to explore this?"
        },
        "🏥 Sick Leave": {
            "title": "Sick Leave",
            "notes": "Hi [Manager Name],\n\nWriting to notify that I am feeling unwell today and will be unable to work. I plan to take a sick day.\n\nProvide coverage detail: [Colleague Name] is briefed on my current tasks and can handle urgent updates.\n\nAvailability: I will check urgent emails intermittently, but will focus on resting.\n\nExpected return: Hope to be back tomorrow."
        },
        "🗓️ Meeting Recap": {
            "title": "Meeting Recap",
            "notes": "Hi team,\n\nThanks for joining today's project review meeting. Here's a recap of the key decisions:\n- Approved the new landing page UI/UX mockups.\n- Postponed the database migration to Q4.\n\nAction items:\n- Vivek: Implement streamlit backend adjustments by Friday.\n- Priya: Review copy content.\n\nNext sync is scheduled for next Monday at 10 AM. Let me know if I missed anything."
        },
        "💰 Salary Negotiation": {
            "title": "Salary Negotiation",
            "notes": "Dear [Hiring Manager Name],\n\nThank you for offering me the role of Senior Developer. I am thrilled about the opportunity to join the team.\n\nState request: Before signing, I would like to discuss the base salary. Given my 5 years of specialized experience in AI systems and the average market rates for this role in London, I was hoping we could explore a base salary of [Target Salary].\n\nReiterate enthusiasm: I am excited about the impact I can deliver and hope we can align on this."
        },
        " Formal Resignation": {
            "title": "Formal Resignation",
            "notes": "Dear [Manager Name],\n\nPlease accept this email as formal notification that I am resigning from my position as [Job Title]. My last day will be [Last Day Date].\n\nExpress gratitude: Thank you for the guidance, mentorship, and opportunities provided during my time here.\n\nTransition offer: I am committed to ensuring a smooth handover of my responsibilities. I will document all current processes and help brief the team before my departure."
        },
        "❌ Polite Decline": {
            "title": "Polite Decline",
            "notes": "Dear [Proposer Name],\n\nThank you for taking the time to share your partnership proposal with us. We appreciate your interest in collaborating.\n\nDeliver decision: After careful review with our executive team, we have decided not to move forward with this opportunity at this time. Our current focus is entirely dedicated to scaling our core software suite, and we do not have the capacity for new integrations.\n\nClosing: We wish you the best of luck with your initiative and hope our paths cross in the future."
        }
    }
    
    # Render templates
    rows = [list(templates.keys())[i:i+3] for i in range(0, len(templates), 3)]
    for row in rows:
        cols = st.columns(3)
        for idx, key in enumerate(row):
            with cols[idx]:
                st.markdown(f"### {key}")
                st.info(templates[key]["notes"][:180] + "...")
                if st.button(f"Load Template: {templates[key]['title']}", key=f"btn_{key}"):
                    st.session_state.raw_notes = templates[key]["notes"]
                    st.toast(f"Loaded outline into workspace!")
                    st.rerun()

# ----------------- Tab 3: AI Inspector -----------------
with tabs[2]:
    st.subheader("📊 Text Inspection & Readability Statistics")
    
    if st.session_state.email_draft:
        metrics = analyze_email_text(st.session_state.email_draft)
        
        # Grid metrics using streamlit's standard columns
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Word Count", metrics['word_count'])
        col_m2.metric("Character Count", metrics['char_count'])
        col_m3.metric("Reading Time", f"{metrics['read_time_min']} min")
        col_m4.metric("Readability Grade", metrics['readability'].split()[0])
        
        st.markdown("---")
        st.markdown("### 🎭 Tone Score Analytics")
        st.write("Calculated analysis of the message attributes:")
        
        st.write("**Professionalism**")
        st.progress(metrics['professionalism'] / 100)
        st.caption(f"Score: {metrics['professionalism']}%")
        
        st.write("**Warmth & Friendliness**")
        st.progress(metrics['warmth'] / 100)
        st.caption(f"Score: {metrics['warmth']}%")
        
        st.write("**Urgency & Focus**")
        st.progress(metrics['urgency'] / 100)
        st.caption(f"Score: {metrics['urgency']}%")
        
        st.markdown("---")
        st.markdown("### ⚠️ Spam Check Analysis")
        if metrics['spam_triggers']:
            st.warning(f"Potential spam words detected: {', '.join(metrics['spam_triggers'])}")
        else:
            st.success("No common marketing spam words detected. Your email should reach primary mailboxes safely!")
    else:
        st.info("No email drafted yet. Metrics will appear here once you generate an email in the Workspace tab.")

# ----------------- Tab 4: System Status -----------------
with tabs[3]:
    st.subheader("⚙️ Connection Status & Diagnostics")
    
    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        st.write("### Gemini API Setup Guide")
        if st.session_state.api_key.strip():
            st.success("Google Gemini API is configured and ready!")
        else:
            st.warning("Google Gemini API Key is missing.")
            
        st.markdown("""
        **How to get a free Gemini API Key:**
        1. Visit [Google AI Studio](https://aistudio.google.com/).
        2. Sign in with your Google account.
        3. Click on **Get API Key** in the top left.
        4. Create a new key and paste it into the **Gemini API Key** field in the sidebar.
        """)
            
    with col_stat2:
        st.write("### System Info")
        st.info("""
        - **Host OS:** Windows
        - **Framework:** Streamlit (Python)
        - **Model Clients:** Google Gemini 1.5 REST API
        - **Theme Settings:** Overridden in `.streamlit/config.toml` (Indigo Dark Theme)
        """)
