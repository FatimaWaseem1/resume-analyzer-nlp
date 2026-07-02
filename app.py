import streamlit as st
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from wordcloud import WordCloud

from utils.extract_text import extract_text_from_pdf
from utils.analyzer import analyze_resume
import utils.analyzer as analyzer_module
st.write("Analyzer file location:", analyzer_module.__file__)


st.set_page_config(page_title="AI Resume Analyzer", page_icon="📄", layout="wide")
st.title("📄 AI Resume Analyzer")
st.write("Upload your resume and a job description to see how well they match.")


def plot_gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Overall Match Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, 40], 'color': "#f8d7da"},
                {'range': [40, 70], 'color': "#fff3cd"},
                {'range': [70, 100], 'color': "#d4edda"}
            ],
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)


def plot_skills_chart(matched, missing):
    fig, ax = plt.subplots(figsize=(4, 3))
    counts = [len(matched), len(missing)]
    labels = ["Matched", "Missing"]
    colors = ["#4CAF50", "#F44336"]
    ax.bar(labels, counts, color=colors)
    ax.set_ylabel("Number of Skills")
    ax.set_title("Skill Match Breakdown")
    for i, v in enumerate(counts):
        ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
    st.pyplot(fig)


def plot_wordcloud(text):
    wc = WordCloud(width=800, height=300, background_color="white", colormap="viridis").generate(text)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)


resume_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])
jd_text = st.text_area("Paste the Job Description here", height=200)

analyze_clicked = st.button("Analyze Resume")


if analyze_clicked:
    if not resume_file:
        st.error("Please upload a resume PDF first.")
    elif not jd_text.strip():
        st.error("Please paste a job description.")
    else:
        with st.spinner("Reading your resume..."):
            resume_text = extract_text_from_pdf(resume_file)

        if not resume_text.strip():
            st.error("Couldn't extract text from this PDF. Try a different file.")
        else:
            with st.spinner("Analyzing..."):
                result = analyze_resume(resume_text, jd_text)
                st.write("DEBUG - Keys in result:", list(result.keys()))

            if "error" in result:
                st.error(result["error"])
            else:
                st.subheader("Match Score")
                plot_gauge(result['match_score'])

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric(label="Semantic Similarity", value=f"{result['semantic_score']}%")
                with col_b:
                    st.metric(label="Keyword Overlap (TF-IDF)", value=f"{result['tfidf_score']}%")

                st.subheader("📋 Resume Health Breakdown")
                col_x, col_y, col_z = st.columns(3)
                with col_x:
                    st.metric("Content Quality", f"{result['content_score']}/100")
                with col_y:
                    st.metric("Formatting", f"{result['format_score']}/100")
                with col_z:
                    st.metric("Keyword Match", f"{result['keyword_score']}/100")

                with st.expander("📐 Structure Check"):
                    if result['sections']['missing_required']:
                        st.warning(f"Missing sections: {', '.join(result['sections']['missing_required'])}")
                    else:
                        st.success("All required sections present (Experience, Education, Skills).")
                    if result['sections']['found_recommended']:
                        st.info(f"Bonus sections found: {', '.join(result['sections']['found_recommended'])}")

                with st.expander("💪 Writing Strength Check"):
                    st.write(f"Strong action verbs used: {result['verbs']['strong_verb_count']}")
                    if result['verbs']['weak_phrases_found']:
                        st.warning(f"Weak phrases detected: {', '.join(result['verbs']['weak_phrases_found'])}")
                    st.write(f"Quantified achievement ratio: {result['achievements']['quantified_ratio']}%")

                with st.expander("📧 Contact Info Check"):
                    st.write(f"Email found: {'✅' if result['contact']['has_email'] else '❌'}")
                    st.write(f"Phone found: {'✅' if result['contact']['has_phone'] else '❌'}")
                    st.write(f"LinkedIn found: {'✅' if result['contact']['has_linkedin'] else '❌'}")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("✅ Matched Skills")
                    if result['matched_skills']:
                        for skill in result['matched_skills']:
                            st.write(f"- {skill}")
                    else:
                        st.write("No direct matches found.")

                with col2:
                    st.subheader("❌ Missing Skills")
                    if result['missing_skills']:
                        for skill in result['missing_skills']:
                            st.write(f"- {skill}")
                    else:
                        st.write("None — great coverage!")

                st.subheader("📊 Skills Breakdown")
                plot_skills_chart(result['matched_skills'], result['missing_skills'])

                st.subheader("☁️ Resume Keyword Cloud")
                plot_wordcloud(resume_text)

                st.subheader("💡 Suggestions")
                for tip in result['suggestions']:
                    st.write(f"- {tip}")

                with st.expander("See extracted resume text"):
                    st.text(resume_text)