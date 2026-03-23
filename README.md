# 🌬️ Air Quality Chatbot (OpenAQ + LLM Demo)

An interactive chat-based air quality assistant powered by:

- 🌍 OpenAQ API (real-time + historical PM2.5 data)
- 🧠 Lightweight LLM-based query understanding
- 📊 Streamlit UI with built-in analysis space (plots + summaries)

---

## 🚀 Demo

### Chat + Current Air Quality
![Demo 1](demo/demo_1.png)

### Historical Comparison + Plot
![Demo 2](demo/demo_2.png)

---

## ✨ Features

### Natural Language Chat
- Current air quality
- Outdoor activity recommendation
- Historical comparison

### Real-Time Data
- OpenAQ API integration
- Nearest station selection

### Visualization
- Time-series plot
- Summary statistics

---

## ⚙️ Setup

```bash
git clone https://github.com/YOUR_USERNAME/air-quality-chatbot.git
cd air-quality-chatbot
pip install -r requirements.txt
```

Create `.env`:

```
OPENAQ_API_KEY=your_api_key_here
```

Run app:

```bash
python -m streamlit run app/streamlit_chat_demo.py
```

---

## 📊 Example Queries

- What is the current air quality in Washington, DC?
- Do you recommend outdoor activity in DC today?
- Compare DC and NYC over the last 10 days

---

## 📌 Author

Junhyun Seo (NASA Goddard Space Flight Center / Morgan State University)
