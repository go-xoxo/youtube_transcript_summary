# Solving PostgreSQL Wicked Problems: Oriole DB Inc - coaJCB_H9cU 🚀🐘🛠️

### 📅 Date: 2022-07-25 | ⏳ Duration: 50:18 | 👁️ Views: 1,260 | 👍 Likes: 25  
### 🎥 Channel: Percona | Video URL: [Watch here](https://www.youtube.com/watch?v=coaJCB_H9cU)  
### 📚 Category: Science & Technology  
### 🏷️ Tags: #PostgreSQL #OpenSource #Databases #OrioleDB #PerconaLive #DatabaseTools #StorageEngines

---

## Summary with 🌟 Highlights & Emojis

### Introduction & Background 👋🐦
- Mehboob Alam and Alexander Korotkov introduce **OrioleDB**, a new storage engine extension for PostgreSQL 🐘.
- PostgreSQL faces longstanding problems like **bloat, xid wraparound, write amplification**, etc. 🐛🕳️
- OrioleDB integrates tightly with PostgreSQL Core using a small patch and provides a new approach to storage 🚧✨.
- The name symbolizes bringing **spring with orioles**, signaling rejuvenation for PostgreSQL’s storage engine 🌸🦜.

### Why Open Source & PostgreSQL? 💻❤️
- Enterprises use multiple databases (average 5-6) causing complexity and cost. OrioleDB aims to make PostgreSQL more powerful to replace some of these 💡🔄.
- Open source is preferred because users want freedom from vendor lock-in and cost 💰✂️.
- PostgreSQL does most things well for many users, trending back towards a general-purpose database 🌍🔥.

### The Storage Engine Challenge 🗄️❄️🔥
- Traditional PostgreSQL storage engine was optimized for spinning hard drives 🕰️💽.
- Modern cloud, SSDs, and memory-based storage require a new model 🌀☁️.
- One-size-fits-all approach is inefficient; users need storage engines tailored for specific workloads 🔧⚙️.

### Existing Alternatives & Limitations ⚖️🔍
- AWS Aurora, GCP's managed Postgres replace the storage engine but are proprietary ☁️🔒.
- Open source projects like YugaByte and CockroachDB hacked PostgreSQL core but don’t fully support extensions or give back improvements 🔧🚧.
- Neon (formerly ZenithDB) is made by PostgreSQL hackers with new ideas but still evolving 🧪.

### OrioleDB’s Solution: Table Access Methods 📦🔌
- PostgreSQL introduced **Table Access Methods** (previously pluggable storage engines) allowing multiple storage engines per table 🧩.
- OrioleDB uses this to implement undo logs, reduce bloat, improve performance, and solve wraparound efficiently 🎯🛡️.
- Undo log moves old versions of rows out of primary storage into separate storage, minimizing bloat 📉🗂️.
- Page merging, garbage collection optimizations allow avoiding the traditional vacuum mechanism 🚮❌.

### Deep Dive: Undo Logs & MVCC 📝🔄
- PostgreSQL’s MVCC keeps multiple versions of rows inside the same heap structure, leading to heavy bloat 📦💥.
- OrioleDB keeps only the latest version in primary storage, old versions in undo logs 🕘.
- This reduces space and improves write amplification significantly ⬇️🔥.
- Large multi-transaction visibility is maintained while avoiding overhead.

### Buffer Mapping & Anti-Buffering Concept 🧠💾
- Traditional databases use page-level caches that require costly lookups for whether a page is already in memory 🔍🧩.
- OrioleDB builds pointers directly inside the index/tree pages leading to **anti-buffering** — skipping lookup overhead, greatly improving scalability ⚡️🏎️.
- This is very important with large memory environments and many CPU cores 🧠⚙️.

### Performance Gains & Benchmarks 📈🎉
- Real-world benchmark shows OrioleDB can handle workloads with **3x throughput** on the same hardware compared to standard PostgreSQL 🔥🚀.
- Write amplification and storage efficiency are vastly improved (especially beneficial for cloud EBS storage costs) 💰☁️.
- OrioleDB also demonstrates better scalability in multi-client scenarios maintaining peak throughput 📊👥.

### Future Directions & Roadmap 🛤️🔮
- OrioleDB patches are on GitHub working with PostgreSQL v13, v14, v15, and aiming for upstream inclusion in v16 🐙📅.
- Not intended to replace PostgreSQL core but to complement it — allows choosing storage engine per workload 🐘🤝.
- Plans for full integration, support for more index types (GIN, etc.), and comprehensive performance regression testing 🔧🧪.
- Also working on making OrioleDB easily usable inside cloud providers and managed services like ScaleGrid to enable sandbox environments ☁️🔧.

### Final Notes & Community 🤗👍
- OrioleDB is open source under the PostgreSQL license ensuring wide adoption without licensing hassles 🚀📜.
- The project aims to bring new horizons to PostgreSQL extensibility much like InnoDB did for MySQL 🏗️🎉.
- Talkers encourage community engagement on GitHub and Twitter for questions and contributions 🗣️💻.
- Exciting next steps include working with new hardware (e.g., persistent memory, Intel Optane), running stable benchmarks, and growing the ecosystem ⚙️💪.

---

## Emojis Recap

- 🐘 PostgreSQL elephant  
- 🦜 Oriole bird (name origin)  
- 🐛 Problematic issues (bloat, etc.)  
- 🔧🛠️ Storage engine solutions  
- 🚀 Performance boost  
- 🧠 CPU & memory optimizations  
- 📈 Benchmarks & scaling  
- 🐙 Open source, GitHub  
- ☁️ Cloud & managed services  
- 🎉 Community & future prospects

---

## Conclusion 🎤  
This talk unveils **OrioleDB**, a cutting-edge PostgreSQL storage engine extension addressing decades-old bottlenecks with innovative use of undo logs and a new buffer mapping approach, promising huge performance and efficiency benefits — all within the open-source PostgreSQL ecosystem. Perfect for DBAs, developers, and database enthusiasts ready for the next level of PostgreSQL technology! 🚀🐘💻

---

Feel free to dive into OrioleDB on GitHub and join the PostgreSQL storage revolution! 🎉🐾