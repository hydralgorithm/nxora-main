"""Generate the synthetic fallback dataset: 1 JD + 18 resumes with KNOWN ground truth.

Tiers: strong (6), partial (6), weak (6). Used for:
  - benchmarking embedding models (bench_models.py)
  - scoring sanity tests (tests/test_scoring.py)
  - demo fallback if the real dataset is unavailable

Run:  python synth_data.py   -> writes ./data/
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

JD = """Junior Full Stack Developer Intern — TechNova Solutions

About the role:
TechNova Solutions is looking for a Junior Full Stack Developer Intern to join our
web engineering team. You will build and ship features across our product: React
frontends, Node.js backend services, and MongoDB data layers.

Responsibilities:
- Build responsive user interfaces with React, HTML, and CSS.
- Develop and maintain REST APIs and backend services using Node.js and Express.
- Design and query document schemas in MongoDB.
- Integrate frontend and backend components through REST APIs.
- Write unit tests for new features and participate in code reviews.
- Collaborate with the team using Git and agile development practices.

Required skills:
- JavaScript (ES6+)
- React
- Node.js
- MongoDB
- HTML and CSS
- REST API development
- Git version control

Nice to have:
- Docker
- AWS
- TypeScript
- Jest or other testing frameworks

Duration: 6 months. stipend Rs. 25,000/month."""

RESUMES: list[dict] = [
    # ---------------- STRONG (6) ----------------
    {
        "file": "resume_S01_Ananya_Sharma.txt", "tier": "strong", "name": "Ananya Sharma",
        "text": """Ananya Sharma
Bengaluru | ananya.sharma@email.com | +91 98XXXXXX01 | github.com/ananyacodes

Summary
Junior full stack developer with hands-on experience building web applications with
JavaScript, React, and Node.js. Comfortable across the stack and shipping features end to end.

Technical Skills
Languages: JavaScript (ES6+), TypeScript, Python
Frontend: React, Redux, HTML5, CSS3, Tailwind CSS
Backend: Node.js, Express, REST APIs, JWT authentication
Databases: MongoDB, MySQL
Tools: Git, GitHub, Docker, Jest, Postman

Experience
Software Engineering Intern — BrightApps (Jun 2025 - Aug 2025)
- Built REST APIs with Express and MongoDB for a food-delivery app serving 2,000 monthly users.
- Developed React components for the customer dashboard, improving load time by 30%.
- Wrote Jest unit tests reaching 80% coverage on new modules.
- Collaborated with 4 engineers using Git flow and agile sprints.

Projects
DevBoard — a Kanban tool (React, Node.js, Express, MongoDB)
- Full stack project with realtime updates, JWT auth, and a Docker-based deployment.
- Designed MongoDB schemas and REST API endpoints for boards, cards, and users.

Education
B.E. Computer Science, Manipal Institute of Technology (2023 - 2027)""",
    },
    {
        "file": "resume_S02_Rohan_Verma.txt", "tier": "strong", "name": "Rohan Verma",
        "text": """ROHAN VERMA
Pune | rohan.verma@email.com | +91 98XXXXXX02

OBJECTIVE
Computer science student seeking full stack web development internship.

SKILLS
JavaScript, React.js, NodeJS, Express.js, MongoDB, HTML, CSS, REST APIs, Git, AWS, Docker

EXPERIENCE
Web Developer Intern — StartupHub (Jan 2025 - Apr 2025)
- Created server-side JavaScript services for an e-commerce checkout flow.
- Built reusable React components and integrated them with RESTful APIs.
- Managed MongoDB collections and wrote aggregation queries for analytics.

PROJECTS
Expense Tracker (MERN stack)
- React frontend with a Node and Express backend, data persisted in MongoDB.
- Deployed on AWS EC2 with Docker containers.

StudyBuddy — study group finder
- RESTful web services, JWT login, responsive CSS design.

EDUCATION
B.Tech Information Technology, VIT Pune (2022 - 2026)""",
    },
    {
        "file": "resume_S03_Priya_Nair.txt", "tier": "strong", "name": "Priya Nair",
        "text": """Priya Nair
Chennai | priya.nair@email.com

Summary
Full stack web developer. I build web apps end to end: React interfaces, Node backends,
and Mongo databases. I like shipping.

Skills
React, Node, Express, MongoDB, JavaScript, HTML/CSS, Git, testing with Jest, TypeScript

Projects
- ChatApp: realtime chat built with Express and WebSockets, front end in React,
  messages stored in MongoDB. 50+ users at my college.
- Portfolio site: responsive HTML and CSS, deployed on Netlify.
- API sandbox: a collection of REST API exercises with Node.js, unit tested with Jest.

Experience
Freelance web developer (2024 - present)
- Delivered 3 client websites: React frontends talking to Node.js REST services.
- Handled deployments and version control with Git and GitHub.

Education
B.Sc. Computer Science, Chennai (2023 - 2026)""",
    },
    {
        "file": "resume_S04_Arjun_Patel.txt", "tier": "strong", "name": "Arjun Patel",
        "text": """Arjun Patel
Mumbai | +91 98XXXXXX04 | arjun.patel@email.com | linkedin.com/in/arjunpatel

EXPERIENCE
Full Stack Developer (Trainee) — CodeCraft Labs (Aug 2024 - Feb 2025)
- Worked on a SaaS dashboard: React frontend, Express.js REST API layer, MongoDB storage.
- Implemented CRUD modules and pagination APIs; wrote integration tests.
- Used Git for version control, participated in agile ceremonies and code reviews.

PROJECTS
- ShopFast: e-commerce demo. React + Redux on the front, Node.js REST services on the
  back, MongoDB for products and orders. Dockerized for local development.
- DevForum: developer Q&A site with RESTful APIs, JWT authentication, HTML/CSS templates.

TECHNICAL SKILLS
JavaScript, TypeScript, React, Node.js, Express, MongoDB, HTML, CSS, Git, Docker, AWS basics, Jest

EDUCATION
B.E. Information Science, Mumbai (2022 - 2026)""",
    },
    {
        "file": "resume_S05_Sneha_Reddy.txt", "tier": "strong", "name": "Sneha Reddy",
        "text": """Sneha Reddy
Hyderabad | sneha.reddy@email.com

Web developer focused on the MERN stack. Experience building REST APIs, React SPAs, and
MongoDB-backed services. Team player, comfortable with Git workflows and agile sprints.

Technical Skills: JavaScript, React, Node.js, Express, MongoDB, HTML5, CSS3, Git, GitHub Actions

Project Experience
- EventLite (hackathon winner, 2025): event booking app. I owned the backend:
  Express REST services with MongoDB, plus the React booking UI. Containerized with Docker.
- Recipio: recipe manager SPA in React with a Node.js API. Wrote unit tests for the API layer.

Work Experience
Web Development Intern — local agency (May 2025 - Jul 2025)
- Built responsive client sites (HTML/CSS/JS) and a small Node.js invoicing API.
- Communicated directly with clients and presented demos each sprint.

Education: B.Tech CSE, Hyderabad (2023 - 2027)""",
    },
    {
        "file": "resume_S06_Kabir_Singh.txt", "tier": "strong", "name": "Kabir Singh",
        "text": """Kabir Singh
Delhi | kabir.singh@email.com | github.com/kabirbuilds

Summary: aspiring full stack engineer; strong on backend services and APIs, solid React.

Skills: Node.js, Express, MongoDB, React, JavaScript, HTML, CSS, Git, Docker, REST API design

Experience
Backend Intern — FinTech startup (remote) (Oct 2024 - Jan 2025)
- Built and maintained RESTful API endpoints in Node.js for a payments dashboard.
- Modeled data in MongoDB; optimized slow queries with indexes.
- Paired with the frontend team to integrate React pages with my APIs.

Projects
- URL shortener service: Node.js + Express + MongoDB, deployed with Docker on AWS.
- Notes app: React frontend, Express backend, full CRUD REST API, versioned with Git.

Education
B.Tech Computer Engineering, Delhi (2022 - 2026)""",
    },

    # ---------------- PARTIAL (6) ----------------
    {
        "file": "resume_P07_Meera_Iyer.txt", "tier": "partial", "name": "Meera Iyer",
        "text": """Meera Iyer
Kochi | meera.iyer@email.com

Summary
Frontend developer with strong React and CSS skills. Some exposure to backend work.

Skills
React, JavaScript, HTML, CSS, Sass, Tailwind, Git, Figma, a bit of Node.js

Experience
Frontend Developer Intern — PixelWorks (Jun 2025 - Sep 2025)
- Built responsive React dashboards from Figma designs.
- Wrote clean HTML/CSS and reusable components; used Git in a team of 5.
- Occasionally fixed small bugs in the company's Node.js services.

Projects
- Design-system playground: React component library with styled CSS.
- Weather app: React frontend consuming a third-party REST API.

Education
B.Des + minor in CS, Kochi (2023 - 2027)""",
    },
    {
        "file": "resume_P08_Vikram_Desai.txt", "tier": "partial", "name": "Vikram Desai",
        "text": """Vikram Desai
Ahmedabad | vikram.desai@email.com

Backend-focused developer. Comfortable with databases and API development; frontend experience is limited.

Technical Skills
Node.js, Express, MongoDB, SQL, MySQL, REST APIs, Git, Linux, Docker

Experience
Backend Intern — DataServe (2024)
- Developed REST API endpoints for an inventory system using Node and Express.
- Wrote MongoDB queries and designed collections.
- Basic HTML admin pages (no modern frontend framework experience).

Projects
- Blog API: Express + MongoDB with authentication; documented REST endpoints.
- SQL migration toolkit: scripts converting MySQL dumps to MongoDB documents.

Education
B.E. Computer Engineering, Gujarat (2022 - 2026)""",
    },
    {
        "file": "resume_P09_Tara_Menon.txt", "tier": "partial", "name": "Tara Menon",
        "text": """Tara Menon
Bangalore | tara.menon@email.com

Summary
CS student with web development coursework and personal projects. Still building depth.

Skills: HTML, CSS, JavaScript, React (basics), Python, MySQL, Git

Projects
- College fest website: responsive HTML/CSS/JS site, small React registration widget.
- Todo app following an online React tutorial; stored tasks with a Node.js tutorial API.
- Coursework: DBMS (SQL), web technologies, data structures.

Education
BCA, Bangalore (2023 - 2026)
Coursework only — no industry internship yet, but I learn fast and love collaborating.""",
    },
    {
        "file": "resume_P10_Dev_Malhotra.txt", "tier": "partial", "name": "Dev Malhotra",
        "text": """Dev Malhotra
Jaipur | dev.malhotra@email.com

Summary
Python/Django web developer exploring the JavaScript ecosystem.

Skills
Python, Django, Flask, JavaScript, HTML, CSS, SQL, PostgreSQL, Git, Docker

Experience
Web Developer — small agency (2024 - 2025)
- Built client sites and admin panels with Django and PostgreSQL.
- Wrote JavaScript for interactivity and some React experiments on personal time.
- Used Git, Docker for deployments.

Projects
- Django e-commerce backend with a REST API (Django REST Framework).
- Learning project: rebuilding my portfolio in React.

Education
B.Tech IT, Jaipur (2021 - 2025)""",
    },
    {
        "file": "resume_P11_Nisha_Gupta.txt", "tier": "partial", "name": "Nisha Gupta",
        "text": """Nisha Gupta
Lucknow | nisha.gupta@email.com

OBJECTIVE: internship in software development.

SKILLS: Java, C++, SQL, HTML, CSS, JavaScript (basic), MySQL, Git

EXPERIENCE:
- College tech fest coordinator (teamwork, communication).
- 2-month lab assistantship: maintained department website (HTML/CSS updates).

PROJECTS:
- Library management system in Java with MySQL database.
- Personal page: basic HTML and CSS site hosted on GitHub Pages.
- Started learning React via online course (50% complete).

EDUCATION: B.Sc. CS, Lucknow (2023 - 2026)""",
    },
    {
        "file": "resume_P12_Aditya_Rao.txt", "tier": "partial", "name": "Aditya Rao",
        "text": """Aditya Rao
Hyderabad | aditya.rao@email.com

Summary
Mobile-first developer with React Native experience; web stack overlap is partial.

Skills
React Native, JavaScript, TypeScript, some React, Firebase, Node.js (basics), Git

Experience
Mobile Developer Intern — AppWorks (2025)
- Built React Native screens consuming REST APIs.
- Used Firebase for auth and data; touched the team's Node.js backend occasionally.

Projects
- Fitness tracker app (React Native, Firebase).
- Web portfolio attempt: React with a Node tutorial backend.

Education
B.Tech ECE, Hyderabad (2022 - 2026)""",
    },

    # ---------------- WEAK (6) ----------------
    {
        "file": "resume_W13_Farhan_Khan.txt", "tier": "weak", "name": "Farhan Khan",
        "text": """Farhan Khan
Kolkata | farhan.khan@email.com

Summary
Data analyst with strong statistics and visualization skills, looking for analytics roles.

Skills
Python, Pandas, NumPy, scikit-learn, SQL, Tableau, Power BI, Excel, machine learning basics

Experience
Data Analyst Intern — RetailCo (2024 - 2025)
- Built dashboards in Tableau and Power BI for sales teams.
- Wrote SQL queries and Python scripts for data cleaning.
- Trained a scikit-learn model to forecast weekly demand.

Projects
- Churn prediction with scikit-learn (Kaggle top 15%).
- Excel automation toolkit for reporting.

Education
B.Com + Data Analytics certification, Kolkata (2022 - 2025)""",
    },
    {
        "file": "resume_W14_Simran_Kaur.txt", "tier": "weak", "name": "Simran Kaur",
        "text": """Simran Kaur
Chandigarh | simran.kaur@email.com

Marketing enthusiast with a flair for content and social media strategy.

Experience
- Social media intern at a D2C brand: ran Instagram campaigns, grew followers 40%.
- Content writer for college magazine; excellent communication skills.
- SEO basics: keyword research, Google Analytics.

Skills: content writing, SEO, Canva, Google Analytics, communication, teamwork

Education
BBA Marketing, Chandigarh (2023 - 2026)""",
    },
    {
        "file": "resume_W15_Rahul_Mishra.txt", "tier": "weak", "name": "Rahul Mishra",
        "text": """Rahul Mishra
Bhopal | rahul.mishra@email.com

Mechanical engineer interested in CAD design and manufacturing.

Skills: AutoCAD, SolidWorks, CATIA, MATLAB, thermodynamics, manufacturing processes

Experience
- Design intern at an automotive component firm: CAD modeling of fixtures.
- Final year project: fatigue analysis of a bracket (ANSYS).

Education
B.E. Mechanical Engineering, Bhopal (2021 - 2025)""",
    },
    {
        "file": "resume_W16_Zoya_Ali.txt", "tier": "weak", "name": "Zoya Ali",
        "text": """Zoya Ali
Mumbai | zoya.ali@email.com

Graphic designer and illustrator.

Skills: Adobe Photoshop, Illustrator, Figma, branding, typography, print design

Experience
- Freelance designer for 8 clients: logos, social media creatives, packaging.
- Design intern at an ad agency: campaign visuals.

Education
BFA Applied Arts, Mumbai (2022 - 2026)""",
    },
    {
        "file": "resume_W17_Nikhil_Joshi.txt", "tier": "weak", "name": "Nikhil Joshi",
        "text": """Nikhil Joshi
Indore | nikhil.joshi@email.com

Fresher. Completed school and a basic computer course. Willing to work hard and learn.

Skills: MS Office, internet browsing, typing 40 wpm, basic HTML (school project)

Education: HSC (2024). Currently preparing for government exams.""",
    },
    {
        "file": "resume_W18_Pooja_Bhatt.txt", "tier": "weak", "name": "Pooja Bhatt",
        "text": """Pooja Bhatt
Nagpur | pooja.bhatt@email.com

HR generalist with recruitment and payroll experience.

Experience
- HR executive: end-to-end recruitment for a 200-person company.
- Payroll processing, onboarding, employee engagement programs.

Skills: recruitment, payroll, HRIS software, communication, Excel

Education
MBA Human Resources, Nagpur (2021 - 2023)""",
    },
]


def main() -> None:
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "jd.txt"), "w", encoding="utf-8") as f:
        f.write(JD)
    manifest = []
    for r in RESUMES:
        with open(os.path.join(DATA, r["file"]), "w", encoding="utf-8") as f:
            f.write(r["text"])
        manifest.append({"file": r["file"], "name": r["name"], "tier": r["tier"]})
    with open(os.path.join(DATA, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(RESUMES)} resumes + jd.txt + manifest.json to {DATA}")


if __name__ == "__main__":
    main()
