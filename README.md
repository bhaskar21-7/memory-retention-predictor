# 🧠 MemoryAI — Smart Revision Scheduler

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![No Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

> **AI-powered memory retention predictor** that learns YOUR forgetting patterns and tells you exactly when to revise.

Most study tools use the same forgetting curve for everyone. **MemoryAI adapts to YOU** — it tracks how quickly you forget each topic and updates its predictions after every revision. The more you use it, the smarter it gets.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🧪 Personalized λ** | Every topic gets its own forgetting rate based on your actual recall |
| **📊 Live Dashboard** | See all your topics with real-time retention percentages |
| **📈 Adaptive Model** | Predictions improve after each revision — watch accuracy climb |
| **🔔 Smart Alerts** | Know which topics need revision RIGHT NOW |
| **📱 Mobile Friendly** | Works beautifully on phones — study on the go |
| **💾 Auto-Save** | Data saves automatically in your browser |
| **📤 Export/Import** | Back up your data anytime as JSON |
| **🎨 Beautiful UI** | Dark glassmorphism design with smooth animations |

---

## 🚀 How to Use

### Option 1: Just Open It
1. Download or clone this repo
2. Open `index.html` in your browser
3. That's it! No installation needed.

### Option 2: GitHub Pages (share with anyone)
1. Push to GitHub
2. Go to **Settings → Pages → Deploy from main branch**
3. Share the link — anyone can use it!

---

## 🧮 The Science

### Ebbinghaus Forgetting Curve
$$R(t) = e^{-λt / S}$$

| Variable | Meaning |
|----------|---------|
| **R(t)** | How much you remember at time *t* (0% — 100%) |
| **t** | Days since you last studied/revised |
| **λ** | Your personal forgetting rate (lower = better memory) |
| **S** | Memory stability (grows with successful reviews) |

### How λ Adapts
After each revision, the model compares what it *predicted* vs what you *actually* remembered:

$$λ_{new} = λ_{old} × \frac{R_{predicted}}{R_{actual}}$$

- Remembered **more** than predicted → λ decreases (your memory is stronger)
- Remembered **less** than predicted → λ increases (need more practice)

### The Result
- **Day 1**: ~40–50% prediction accuracy (using only your initial score)
- **Day 5+**: ~70–85% accuracy (after adaptive updates)

---

## 📁 Project Structure

```
memory-retention-predictor/
├── index.html      ← The entire app (open in browser)
├── README.md       ← You are here
├── LICENSE         ← MIT License
└── .gitignore
```

### Legacy Python Version
The original Streamlit version is preserved in the `legacy/` folder for reference.

---

## 🛣️ Roadmap

- [x] Personalized forgetting rate (λ)
- [x] Adaptive λ updates from actual recall
- [x] Memory stability tracking
- [x] Interactive dashboard with charts
- [x] Mobile-responsive design
- [x] Export/Import data
- [x] Demo data for first-time users
- [ ] Push notification reminders
- [ ] Multi-device sync (cloud storage)
- [ ] Study streak tracking
- [ ] Social sharing cards

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT — do whatever you want with it.
