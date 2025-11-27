import fitz  # PyMuPDF
import re

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Read the uploaded PDF (Streamlit file_uploader object) and return full text.
    """
    file_bytes = uploaded_file.read()
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text() # type: ignore
    return text


def _find_name(lines):
    """
    Name detection heuristic
    """
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        lower = clean.lower()
        if "resume" in lower or "curriculum vitae" in lower or lower == "cv":
            continue
        if 2 <= len(clean.split()) <= 5:
            return clean
        return clean
    return ""


def extract_basic_info(text: str) -> dict:
    text = text.replace("\r", "\n")
    lines = [l.strip() for l in text.split("\n")]

    # ---- Name ----
    name = _find_name(lines)

    # ---- Email ----
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    email = email_match.group(0) if email_match else ""

    # ---- Contact / Phone ----
    phone_match = re.search(r"(\+?\d[\d\-\s]{8,}\d)", text)
    contact = phone_match.group(0).strip() if phone_match else ""

    # ✅ IMPROVED LINKEDIN EXTRACTION
    linkedin = ""
    for line in lines:
        if "linkedin" in line.lower():
            url_match = re.search(r"(https?://[^\s]*linkedin\.com[^\s]*)", line, re.IGNORECASE)
            if url_match:
                linkedin = url_match.group(0)
            else:
                txt = line.split(":")[-1].strip()
                if "linkedin" in txt.lower():
                    linkedin = txt
            break

    # ---- GitHub ----
    github_match = re.search(r"(https?://[^\s]*github\.com[^\s]*)", text, re.IGNORECASE)
    github = github_match.group(0) if github_match else ""

    # ---- Skills ----
    skills = ""
    skills_pattern = re.compile(r"(skills|technical skills)\s*[:\-]?\s*(.*)", re.IGNORECASE)
    for i, line in enumerate(lines):
        m = skills_pattern.search(line)
        if m:
            if m.group(2).strip():
                skills = m.group(2).strip()
            else:
                for nxt in lines[i+1:]:
                    if nxt.strip():
                        skills = nxt.strip()
                        break
            break

    # ✅ EDUCATION EXTRACTION
    education = []
    edu_idx = None

    for i, line in enumerate(lines):
        if "education" in line.lower():
            edu_idx = i
            break

    if edu_idx is not None:
        for line in lines[edu_idx+1:]:
            if line.isupper() and len(line.split()) < 5:
                break

            degree_match = re.search(r"(B\.?Tech|BTech|B\.?E\.?|M\.?Tech|Diploma|Bachelor|Master|Class\s?\d{2}).*", line, re.IGNORECASE)
            cgpa_match = re.search(r"(CGPA|GPA)[^\d]*([\d\.]+)", line, re.IGNORECASE)
            perc_match = re.search(r"(\d{2,3}\s?%)", line)
            year_match = re.search(r"(20\d{2}[-–]\s?20\d{2}|20\d{2})", line)

            if degree_match:
                education.append({
                    "degree": degree_match.group(0).strip(),
                    "cgpa": cgpa_match.group(2) if cgpa_match else "",
                    "percentage": perc_match.group(1) if perc_match else "",
                    "year": year_match.group(0) if year_match else ""
                })

    return {
        "name": name,
        "email": email,
        "contact": contact,
        "skills": skills,
        "linkedin": linkedin,
        "github": github,
        "education": education,
        "achievements": [],
        "certifications": [],
        "projects": [],
    }
