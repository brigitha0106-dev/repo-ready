import streamlit as st
import time
from analyzer import analyze_project
from report import generate_report

st.set_page_config(
    page_title="RepoReady",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Custom styling ----------
st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }
    .hero {
        padding: 2.2rem 2rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        margin-bottom: 1.5rem;
    }
    .hero h1 {
        margin: 0 0 0.3rem 0;
        font-size: 2.1rem;
    }
    .hero p {
        margin: 0;
        opacity: 0.92;
        font-size: 1.05rem;
    }
    .feature-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.1rem 1.2rem;
        height: 100%;
    }
    .feature-card h4 {
        margin: 0 0 0.4rem 0;
        font-size: 1rem;
    }
    .feature-card p {
        margin: 0;
        font-size: 0.88rem;
        color: #6b7280;
    }
    .upload-box {
        border-radius: 14px;
        padding: 1.5rem;
        background: #fafafa;
        border: 1px dashed #d1d5db;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### 🚀 RepoReady")
    st.caption("Codebase understanding, before you touch a line of code.")
    st.divider()
    st.markdown("**What gets analyzed**")
    st.markdown(
        "- 📁 Project structure\n"
        "- 📄 Documentation\n"
        "- 📦 Dependencies\n"
        "- 🧪 Tests\n"
        "- 📝 Dev notes"
    )
    st.divider()
    st.caption("Your ZIP is analyzed for this session only.")

# ---------- Hero ----------
st.markdown(
    """
    <div class="hero">
        <h1>🚀 RepoReady</h1>
        <p>Understand a codebase before you start coding.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- Feature highlights ----------
cols = st.columns(5)
features = [
    ("📁", "Structure", "Map out folders & key files"),
    ("📄", "Docs", "Summarize README & guides"),
    ("📦", "Dependencies", "List packages & versions"),
    ("🧪", "Tests", "Spot test coverage gaps"),
    ("📝", "Dev Notes", "Surface TODOs & comments"),
]
for col, (icon, title, desc) in zip(cols, features):
    with col:
        st.markdown(
            f"""
            <div class="feature-card">
                <h4>{icon} {title}</h4>
                <p>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.write("")
st.divider()

# ---------- Upload section ----------
st.markdown("### Upload your project")

left, right = st.columns([2, 1])

with left:
    uploaded_file = st.file_uploader(
        "Drop a ZIP file here or click to browse",
        type=["zip"],
        help="Only .zip files are supported, max recommended size 200MB."
    )

st.markdown(
    """
    <div class="upload-box">
    <b>Tips</b><br><br>
    • Include a README if you have one<br>
    • Exclude large dependency folders<br>
    • Include requirements.txt or package.json if available
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- Post-upload state ----------
# ---------- Post-upload state ----------

if uploaded_file:
    file_size_mb = uploaded_file.size / (1024 * 1024)

    st.success(
        f"✅ **{uploaded_file.name}** uploaded ({file_size_mb:.1f} MB)"
    )

    col_a, col_b = st.columns([1, 4])

    with col_a:
        analyze_clicked = st.button(
            "🔍 Analyze Project",
            type="primary",
            use_container_width=True
        )

    with col_b:
        st.caption(
            "This usually takes a few seconds depending on repo size."
        )

    if analyze_clicked:

        with st.spinner("🔍 Analyzing project..."):
            results = analyze_project(uploaded_file)
            report = generate_report(results)

        st.success("✅ Analysis complete!")

        st.divider()

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Files",
                len(results["files"])
            )

        with col2:
            st.metric(
                "Directories",
                len(results["directories"])
            )

        with col3:
            st.metric(
                "TODOs",
                results["todo_count"]
            )

        with col4:
            st.metric(
                "FIXMEs",
                results["fixme_count"]
            )

        st.divider()

        # Results tabs — Readiness Report is first
        tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "📋 Readiness Report",
                "📁 Structure",
                "📄 Docs",
                "📦 Dependencies",
                "🧪 Tests",
                "📝 Dev Notes",
            ]
        )

        # ── Readiness Report ──────────────────────────────────────────────
        with tab0:
            score = report["readiness_score"]["score"]
            max_score = report["readiness_score"]["max"]
            status = report["readiness_status"]
            project_type = report["project_type"]

            # Status banner
            status_icon = {"Ready": "🟢", "Needs Attention": "🟡", "Not Ready": "🔴"}.get(status, "⚪")
            banner_fn = {"Ready": st.success, "Needs Attention": st.warning, "Not Ready": st.error}.get(
                status, st.info
            )
            banner_fn(
                f"{status_icon} **{status}** — "
                f"Readiness score: **{score}/{max_score}** · "
                f"Project type: **{project_type}**"
            )

            st.write("")

            # ── Start Here ────────────────────────────────────────────────
            st.subheader("🚦 Start Here")
            st.caption(
                "These are the three most important things to do before making changes to this repository."
            )

            step_colors = {
                "FIRST": st.error,
                "SECOND": st.warning,
                "THIRD": st.info,
            }

            for item in report["start_here"]:
                step_label = item.get("step", "")
                action = item.get("action", "")
                reason = item.get("reason", "")
                render = step_colors.get(step_label, st.info)
                render(f"**{step_label}: {action}**  \n{reason}")

            st.divider()

            # ── Findings columns ──────────────────────────────────────────
            col_good, col_concern = st.columns(2)

            with col_good:
                st.markdown("**✅ What's in good shape**")
                strengths = report["strengths"]
                if strengths:
                    for s in strengths:
                        st.markdown(f"- {s}")
                else:
                    st.caption("No clear strengths detected.")

            with col_concern:
                st.markdown("**⚠️ What needs attention**")
                concerns = report["concerns"]
                if concerns:
                    for c in concerns:
                        st.markdown(f"- {c}")
                else:
                    st.success("Nothing critical — this repo is well set up.")

            # ── IBM Bob Integration ───────────────────────────────────────
            st.divider()
            st.markdown(
                """
                <div style="
                    background:#1e1e2e;
                    border:1px solid #374151;
                    border-radius:10px;
                    padding:1rem 1.2rem;
                    margin:0.4rem 0 0 0;
                ">
                    <p style="margin:0 0 0.4rem 0; font-size:1rem; font-weight:600; color:#e2e8f0;">
                        🤖 IBM Bob Integration
                    </p>
                    <p style="margin:0 0 0.6rem 0; font-size:0.88rem; color:#94a3b8; line-height:1.5;">
                        RepoReady works with IBM Bob to help developers
                        understand, investigate, and improve unfamiliar codebases.
                    </p>
                    <span style="
                        display:inline-block;
                        background:#052e16;
                        color:#34d399;
                        border:1px solid #166534;
                        border-radius:6px;
                        padding:0.2rem 0.65rem;
                        font-size:0.78rem;
                        font-weight:600;
                    ">&#10003; Connected through MCP</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Structure ─────────────────────────────────────────────────────
        with tab1:
            st.subheader("Project Structure")

            st.write(
                f"**{len(results['files'])} files** "
                f"and **{len(results['directories'])} directories** found."
            )

            st.write("### Files")

            for file in results["files"]:
                st.write(f"📄 {file}")

        # ── Documentation ─────────────────────────────────────────────────
        with tab2:
            st.subheader("Documentation")

            if results["readme"]:
                st.success("README file found.")
            else:
                st.warning("README file not found.")

        # ── Dependencies ──────────────────────────────────────────────────
        with tab3:
            st.subheader("Dependencies")

            if results["dependencies"]:
                st.success("Dependency files found.")

                for dependency in results["dependencies"]:
                    st.write(f"📦 {dependency}")
            else:
                st.warning("No dependency file detected.")

        # ── Tests ─────────────────────────────────────────────────────────
        with tab4:
            st.subheader("Tests")

            if results["tests"]:
                st.success(
                    f"{len(results['tests'])} possible test files found."
                )

                for test in results["tests"]:
                    st.write(f"🧪 {test}")
            else:
                st.warning("No test files detected.")

        # ── Development Notes ─────────────────────────────────────────────
        with tab5:
            st.subheader("Development Notes")

            st.write(
                f"TODO comments: **{results['todo_count']}**"
            )

            st.write(
                f"FIXME comments: **{results['fixme_count']}**"
            )

else:
    st.info("👆 Upload a ZIP file to get started.")