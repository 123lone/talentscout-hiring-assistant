# TalentScout — AI Hiring Assistant

A smart, conversational AI recruiter built using **Streamlit**, **OpenAI**, and a clean, modern chat UI. This assistant conducts candidate screenings, collects personal details, and generates technical questions based on the candidate's tech stack.

---

## 🚀 Features

* AI-powered conversational hiring assistant
* Collects candidate info (name, experience, role, skills, etc.)
* Generates technical MCQs, coding challenges, conceptual questions
* Clean chat-style UI with bubbles
* Supports **OpenAI live mode** and fallback **mock mode** if no key is set
* Saves submissions locally as JSON
* Deployable on Streamlit Cloud / GitHub

---

## 📂 Project Structure

```
├── app.py                 # Streamlit UI
├── logic.py               # Chat flow and OpenAI logic
├── prompts.py             # System prompts and message templates
├── utils.py               # Environment + helper utilities
├── requirements.txt       # Dependencies
├── data/
│   └── submissions.json   # Saved candidate data
└── README.md
```

---

## 🔧 Prerequisites

* Python **3.11** (recommended for Streamlit + OpenAI compatibility)
* Git (for version control)
* OpenAI API Key (optional; app works in mock mode without it)

---

## ⚙️ Installation

### 1. Clone the Repository

```
git clone https://github.com/YOUR_USERNAME/talentscout-hiring-assistant.git
cd talentscout-hiring-assistant
```

### 2. Create Virtual Environment (Windows)

```
py -3.11 -m venv venv
venv\Scripts\activate
```

Mac/Linux:

```
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

---

## 🔑 Setting Your OpenAI API Key

You can run the app in **two modes**:

### ✔ Live Mode (OpenAI)

Set your key in your terminal before running Streamlit:

Windows (PowerShell):

```
setx OPENAI_API_KEY "you
```
