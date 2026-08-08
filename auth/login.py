import os
import streamlit as st
from database.supabase_client import supabase, supabase_admin
import streamlit.components.v1 as components


# ============================================================
# Pakistan Locations Dictionary
# ============================================================

PAK_LOCATIONS = {
    "Punjab": [
        "Lahore",
        "Rawalpindi",
        "Faisalabad",
        "Multan",
        "Gujranwala",
        "Sialkot",
        "Bahawalpur",
        "Sargodha",
        "Gujrat",
        "Sheikhupura"
    ],
    "Sindh": [
        "Karachi",
        "Hyderabad",
        "Sukkur",
        "Larkana",
        "Nawabshah",
        "Mirpur Khas"
    ],
    "Khyber Pakhtunkhwa (KP)": [
        "Peshawar",
        "Abbottabad",
        "Mardan",
        "Swat",
        "Kohat",
        "Dera Ismail Khan"
    ],
    "Balochistan": [
        "Quetta",
        "Gwadar",
        "Turbat",
        "Khuzdar",
        "Sibi"
    ],
    "Islamabad Capital Territory": [
        "Islamabad"
    ],
    "Gilgit-Baltistan": [
        "Gilgit",
        "Skardu",
        "Hunza"
    ],
    "Azad Kashmir": [
        "Muzaffarabad",
        "Mirpur",
        "Rawalakot"
    ]
}


# ============================================================
# LOGIN PAGE
# ============================================================

def render_login_page():

    # ========================================================
    # PREMIUM LOGIN CSS
    # CSS IS NOW EMBEDDED DIRECTLY IN THIS FILE
    # ========================================================

    st.markdown(
        """
        <style>

        /* =====================================================
           GOOGLE FONT
           ===================================================== */

        @import url(
            'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap'
        );


        /* =====================================================
           ROOT VARIABLES
           ===================================================== */

        :root {
            --primary: #3B82F6;
            --primary-dark: #2563EB;
            --secondary: #06B6D4;
            --accent: #8B5CF6;

            --success: #22C55E;
            --warning: #F59E0B;
            --danger: #EF4444;

            --text: #FFFFFF;
            --muted: #E2E8F0;

            --border: rgba(255,255,255,0.18);

            --shadow:
                0 20px 60px rgba(0,0,0,0.35);
        }


        /* =====================================================
           GLOBAL FONT
           ===================================================== */

        html,
        body,
        .stApp {
            font-family: "Poppins", sans-serif !important;
        }


        /* =====================================================
           APP BACKGROUND
           ===================================================== */

        .stApp {
            background:
                radial-gradient(
                    circle at top left,
                    #1E3A8A 0%,
                    transparent 35%
                ),
                radial-gradient(
                    circle at bottom right,
                    #7C3AED 0%,
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    #071226,
                    #0F172A,
                    #111827
                ) !important;

            background-size: cover !important;
            background-attachment: fixed !important;

            color: #FFFFFF !important;

            min-height: 100vh;
        }


        /* =====================================================
           ANIMATED BACKGROUND
           ===================================================== */

        .stApp::before {
            content: "";

            position: fixed;

            width: 700px;
            height: 700px;

            top: -180px;
            left: -180px;

            background: rgba(59,130,246,0.12);

            filter: blur(140px);

            animation: floatOne 18s infinite alternate;

            z-index: 0;

            pointer-events: none;
        }


        .stApp::after {
            content: "";

            position: fixed;

            width: 600px;
            height: 600px;

            bottom: -150px;
            right: -120px;

            background: rgba(139,92,246,0.18);

            filter: blur(150px);

            animation: floatTwo 16s infinite alternate;

            z-index: 0;

            pointer-events: none;
        }


        @keyframes floatOne {

            0% {
                transform: translate(0, 0);
            }

            50% {
                transform: translate(120px, 80px);
            }

            100% {
                transform: translate(40px, 180px);
            }
        }


        @keyframes floatTwo {

            0% {
                transform: translate(0, 0);
            }

            100% {
                transform: translate(-130px, -110px);
            }
        }


        /* =====================================================
           STREAMLIT UI HIDE
           ===================================================== */

        #MainMenu {
            visibility: hidden !important;
        }

        footer {
            visibility: hidden !important;
        }

        header {
            visibility: hidden !important;
        }


        /* =====================================================
           MAIN CONTAINER
           ===================================================== */

        .main .block-container {
            max-width: 760px !important;

            padding-top: 55px !important;
            padding-bottom: 70px !important;

            animation: fadeUp 0.8s ease;

            position: relative;
            z-index: 1;
        }


        /* =====================================================
           TITLE
           ===================================================== */

        h1 {
            text-align: center !important;

            font-size: 42px !important;

            font-weight: 800 !important;

            letter-spacing: 0.5px;

            margin-bottom: 35px !important;

            background:
                linear-gradient(
                    90deg,
                    #FFFFFF,
                    #60A5FA,
                    #C084FC
                );

            -webkit-background-clip: text !important;
            background-clip: text !important;

            -webkit-text-fill-color: transparent !important;

            color: transparent !important;
        }


        /* =====================================================
           HEADINGS
           ===================================================== */

        h2,
        h3,
        h4,
        h5,
        h6 {
            color: #FFFFFF !important;
        }

        h3 {
            font-weight: 700 !important;
            font-size: 26px !important;
            margin-bottom: 20px !important;
        }


        /* =====================================================
           LABELS
           ===================================================== */

        label {
            font-weight: 600 !important;
            font-size: 15px !important;

            color: #FFFFFF !important;
        }


        /* =====================================================
           TEXT INPUTS
           ===================================================== */

        .stTextInput input {
            background: #FFFFFF !important;

            color: #111827 !important;

            -webkit-text-fill-color: #111827 !important;

            border: 1px solid #D1D5DB !important;

            border-radius: 12px !important;

            padding: 13px 16px !important;

            font-size: 15px !important;

            transition:
                border-color 0.25s ease,
                box-shadow 0.25s ease,
                transform 0.25s ease !important;
        }


        .stTextInput input::placeholder {
            color: #6B7280 !important;

            opacity: 1 !important;
        }


        .stTextInput input:hover {
            border-color: #60A5FA !important;
        }


        .stTextInput input:focus {
            border-color: #3B82F6 !important;

            -webkit-text-fill-color: #111827 !important;

            box-shadow:
                0 0 0 4px rgba(96,165,250,0.18) !important;

            background: #FFFFFF !important;
        }


        .stTextInput:focus-within {
            transform: translateY(-2px);
        }


        /* =====================================================
           PASSWORD INPUT
           ===================================================== */

        input[type="password"] {
            color: #111827 !important;

            -webkit-text-fill-color: #111827 !important;

            font-weight: 600 !important;

            letter-spacing: 2px !important;
        }


        /* =====================================================
           SELECTBOX
           ===================================================== */

        div[data-baseweb="select"] > div {
            background: #FFFFFF !important;

            color: #111827 !important;

            border: 1px solid #D1D5DB !important;

            border-radius: 12px !important;
        }


        div[data-baseweb="select"] span {
            color: #111827 !important;
        }


        div[data-baseweb="select"] svg {
            color: #111827 !important;

            fill: #111827 !important;
        }


        /* =====================================================
           DROPDOWN POPUP
           ===================================================== */

        div[data-baseweb="popover"],
        div[data-baseweb="menu"],
        ul[role="listbox"],
        div[role="listbox"] {
            background-color: #FFFFFF !important;

            border-radius: 10px !important;
        }


        div[data-baseweb="popover"] *,
        div[data-baseweb="menu"] *,
        ul[role="listbox"] *,
        div[role="listbox"] * {
            color: #111827 !important;
        }


        div[data-baseweb="popover"] [role="option"],
        ul[role="listbox"] li {
            background-color: #FFFFFF !important;

            color: #111827 !important;
        }


        div[data-baseweb="popover"] [role="option"]:hover,
        ul[role="listbox"] li:hover,
        div[role="option"]:hover {
            background-color: #F3F4F6 !important;

            color: #111827 !important;
        }


        /* =====================================================
           CHECKBOX
           ===================================================== */

        .stCheckbox {
            margin-top: 8px;
            margin-bottom: 18px;
        }


        .stCheckbox label {
            font-size: 14px !important;

            color: #FFFFFF !important;
        }


        .stCheckbox input {
            cursor: pointer;
        }


        .stCheckbox:hover {
            transform: translateX(2px);

            transition: 0.25s ease;
        }


        /* =====================================================
           TABS
           ===================================================== */

        .stTabs {
            margin-top: 20px;
        }


        .stTabs [data-baseweb="tab-list"] {
            gap: 10px !important;

            background: rgba(255,255,255,0.06) !important;

            padding: 8px !important;

            border-radius: 16px !important;
        }


        .stTabs [data-baseweb="tab"] {
            background: transparent !important;

            color: #FFFFFF !important;

            font-size: 15px !important;

            font-weight: 600 !important;

            padding: 14px 24px !important;

            border-radius: 12px !important;

            transition: 0.3s ease !important;
        }


        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255,255,255,0.08) !important;

            color: #FFFFFF !important;
        }


        .stTabs [aria-selected="true"] {
            background:
                linear-gradient(
                    135deg,
                    #3B82F6,
                    #8B5CF6
                ) !important;

            color: #FFFFFF !important;

            box-shadow:
                0 8px 24px rgba(59,130,246,0.4) !important;
        }


        /* =====================================================
           BUTTONS
           ===================================================== */

        .stButton {
            position: relative;

            animation: buttonFade 0.6s ease;
        }


        .stButton > button {
            width: 100% !important;

            border: none !important;

            border-radius: 14px !important;

            padding: 14px !important;

            font-size: 16px !important;

            font-weight: 700 !important;

            color: #FFFFFF !important;

            -webkit-text-fill-color: #FFFFFF !important;

            cursor: pointer !important;

            background:
                linear-gradient(
                    135deg,
                    #2563EB,
                    #8B5CF6
                ) !important;

            transition:
                transform 0.25s ease,
                box-shadow 0.25s ease,
                filter 0.25s ease !important;

            box-shadow:
                0 15px 35px rgba(59,130,246,0.35) !important;

            overflow: hidden !important;
        }


        .stButton > button:hover {
            transform: translateY(-3px) !important;

            box-shadow:
                0 22px 42px rgba(59,130,246,0.45) !important;

            background:
                linear-gradient(
                    135deg,
                    #3B82F6,
                    #9333EA
                ) !important;

            filter: brightness(108%);
        }


        .stButton > button:active {
            transform: scale(0.98) !important;
        }


        /* =====================================================
           BUTTON RIPPLE
           ===================================================== */

        .stButton > button::after {
            content: "";

            position: absolute;

            width: 0;
            height: 0;

            top: 50%;
            left: 50%;

            background: rgba(255,255,255,0.25);

            border-radius: 50%;

            transform: translate(-50%, -50%);

            transition: 0.6s;
        }


        .stButton > button:hover::after {
            width: 420px;
            height: 420px;

            opacity: 0;
        }


        /* =====================================================
           ALERTS
           ===================================================== */

        [data-testid="stAlert"] {
            border-radius: 16px !important;

            padding: 14px 18px !important;

            margin-top: 15px !important;

            margin-bottom: 15px !important;

            box-shadow:
                0 12px 28px rgba(0,0,0,0.25) !important;
        }


        .stSuccess {
            background: rgba(34,197,94,0.15) !important;

            border: 1px solid rgba(34,197,94,0.45) !important;

            border-left: 5px solid #22C55E !important;

            border-radius: 14px !important;

            color: #FFFFFF !important;

            animation: fadeAlert 0.45s ease;
        }


        .stError {
            background: rgba(239,68,68,0.15) !important;

            border: 1px solid rgba(239,68,68,0.45) !important;

            border-left: 5px solid #EF4444 !important;

            border-radius: 14px !important;

            color: #FFFFFF !important;

            animation: fadeAlert 0.45s ease;
        }


        .stWarning {
            background: rgba(245,158,11,0.15) !important;

            border: 1px solid rgba(245,158,11,0.45) !important;

            border-left: 5px solid #F59E0B !important;

            border-radius: 14px !important;

            color: #FFFFFF !important;

            animation: fadeAlert 0.45s ease;
        }


        .stInfo {
            background: rgba(59,130,246,0.15) !important;

            border: 1px solid rgba(59,130,246,0.40) !important;

            border-left: 5px solid #3B82F6 !important;

            border-radius: 14px !important;

            color: #FFFFFF !important;

            animation: fadeAlert 0.45s ease;

            backdrop-filter: blur(18px);
        }


        /* =====================================================
           ALERT ANIMATION
           ===================================================== */

        @keyframes fadeAlert {

            from {
                opacity: 0;
                transform: translateY(12px);
            }

            to {
                opacity: 1;
                transform: translateY(0);
            }
        }


        /* =====================================================
           SPINNER
           ===================================================== */

        [data-testid="stSpinner"] {
            color: #60A5FA !important;
        }


        /* =====================================================
           DIVIDER
           ===================================================== */

        hr {
            border: none !important;

            height: 1px !important;

            background: rgba(255,255,255,0.08) !important;

            margin: 25px 0 !important;
        }


        /* =====================================================
           COLUMNS
           ===================================================== */

        [data-testid="column"] {
            padding-top: 10px;
        }


        /* =====================================================
           SCROLLBAR
           ===================================================== */

        ::-webkit-scrollbar {
            width: 10px;
        }


        ::-webkit-scrollbar-track {
            background: #0F172A;
        }


        ::-webkit-scrollbar-thumb {
            background:
                linear-gradient(
                    180deg,
                    #3B82F6,
                    #8B5CF6
                );

            border-radius: 20px;
        }


        ::-webkit-scrollbar-thumb:hover {
            background: #60A5FA;
        }


        /* =====================================================
           SELECTION
           ===================================================== */

        ::selection {
            background: #3B82F6;

            color: #FFFFFF;
        }


        /* =====================================================
           ANIMATIONS
           ===================================================== */

        @keyframes fadeUp {

            from {
                opacity: 0;

                transform: translateY(40px);
            }

            to {
                opacity: 1;

                transform: translateY(0);
            }
        }


        @keyframes buttonFade {

            from {
                opacity: 0;

                transform: scale(0.95);
            }

            to {
                opacity: 1;

                transform: scale(1);
            }
        }


        /* =====================================================
           RESPONSIVE - TABLET
           ===================================================== */

        @media screen and (max-width: 992px) {

            .main .block-container {
                padding-left: 25px !important;

                padding-right: 25px !important;
            }


            h1 {
                font-size: 34px !important;
            }


            h3 {
                font-size: 22px !important;
            }
        }


        /* =====================================================
           RESPONSIVE - MOBILE
           ===================================================== */

        @media screen and (max-width: 768px) {

            .main .block-container {
                max-width: 100% !important;

                padding-top: 20px !important;
            }


            .stTabs [data-baseweb="tab"] {
                padding: 12px !important;

                font-size: 14px !important;
            }


            .stButton > button {
                padding: 13px !important;
            }


            h1 {
                font-size: 28px !important;
            }
        }


        /* =====================================================
           RESPONSIVE - SMALL MOBILE
           ===================================================== */

        @media screen and (max-width: 480px) {

            .main .block-container {
                padding-left: 12px !important;

                padding-right: 12px !important;
            }


            h1 {
                font-size: 24px !important;
            }


            h3 {
                font-size: 20px !important;
            }


            .stTextInput input {
                padding: 13px !important;
            }
        }


        </style>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # DROPDOWN MENU TEXT FIX
    # ========================================================

    components.html(
        """
        <script>
        const observer = new MutationObserver((mutations) => {

            document.querySelectorAll(
                '[data-baseweb="popover"] div[role="option"], ' +
                '[data-baseweb="menu"] div, ' +
                'ul[role="listbox"] li'
            ).forEach(el => {

                el.style.color = '#111827';

                el.style.backgroundColor = '#FFFFFF';

            });

        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        </script>
        """,
        height=0
    )


    # ========================================================
    # PAGE TITLE
    # ========================================================

    st.title("👁️ Urban Eye AI - Security Portal")


    # ========================================================
    # 1. PASSWORD RESET STATE INITIALIZATION
    # ========================================================

    if "reset_verified" not in st.session_state:
        st.session_state["reset_verified"] = False

    if "reset_target_user_id" not in st.session_state:
        st.session_state["reset_target_user_id"] = None

    if "reset_matched_email" not in st.session_state:
        st.session_state["reset_matched_email"] = ""


    # ========================================================
    # 2. AUTO-LOGIN RECOVERY
    # KEEP ME LOGGED IN
    # ========================================================

    if (
        "user" not in st.session_state
        or st.session_state["user"] is None
    ):

        if (
            "logged_in_email" in st.query_params
            and supabase_admin
        ):

            try:

                saved_email = st.query_params[
                    "logged_in_email"
                ]

                res = (
                    supabase_admin
                    .table("profiles")
                    .select("*")
                    .eq(
                        "email",
                        saved_email.strip().lower()
                    )
                    .execute()
                )

                if res.data and len(res.data) > 0:

                    profile = res.data[0]

                    st.session_state["user_profile"] = {
                        "email": profile.get(
                            "email",
                            saved_email
                        ),

                        "username": profile.get(
                            "username",
                            "Inspector Ahmed"
                        ),

                        "phone": profile.get(
                            "phone",
                            "+92 300 1234567"
                        ),

                        "address": profile.get(
                            "address",
                            "Lahore, Punjab, Pakistan"
                        ),
                    }

            except Exception:
                pass


    # ========================================================
    # TABS
    # ========================================================

    tab_login, tab_signup, tab_forgot = st.tabs(
        [
            "🔑 Login",
            "📝 Sign Up",
            "❓ Forgot Password"
        ]
    )


    # ========================================================
    # LOGIN TAB
    # ========================================================

    with tab_login:

        st.subheader("Login to your account")


        email = st.text_input(
            "Email Address",
            key="login_email"
        )


        password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )


        remember_me = st.checkbox(
            "Keep me logged in",
            key="login_remember_me"
        )


        if st.button(
            "Sign In",
            key="btn_login",
            use_container_width=True
        ):

            if not email or not password:

                st.warning(
                    "Please enter both Email and Password!"
                )

            else:

                try:

                    response = (
                        supabase.auth.sign_in_with_password(
                            {
                                "email": email,
                                "password": password
                            }
                        )
                    )


                    st.session_state["user"] = (
                        response.user
                    )


                    # ----------------------------------------
                    # KEEP ME LOGGED IN
                    # ----------------------------------------

                    if remember_me:

                        st.query_params[
                            "logged_in_email"
                        ] = email

                    else:

                        if (
                            "logged_in_email"
                            in st.query_params
                        ):

                            del st.query_params[
                                "logged_in_email"
                            ]


                    # ----------------------------------------
                    # GET PROFILE
                    # ----------------------------------------

                    res = (
                        supabase
                        .table("profiles")
                        .select("*")
                        .eq(
                            "email",
                            email.strip().lower()
                        )
                        .execute()
                    )


                    if res.data and len(res.data) > 0:

                        profile = res.data[0]

                        st.session_state[
                            "user_profile"
                        ] = {

                            "email": profile.get(
                                "email",
                                email
                            ),

                            "username": profile.get(
                                "username",
                                "Inspector Ahmed"
                            ),

                            "phone": profile.get(
                                "phone",
                                "+92 300 1234567"
                            ),

                            "address": profile.get(
                                "address",
                                "Lahore, Punjab, Pakistan"
                            ),
                        }


                    st.success(
                        "✅ Login successful!"
                    )

                    st.rerun()


                except Exception as e:

                    st.error(
                        f"❌ Login failed: {e}"
                    )


    # ========================================================
    # SIGN UP TAB
    # ========================================================

    with tab_signup:

        st.subheader("Create a new account")


        username = st.text_input(
            "Full Name / Username",
            key="signup_username"
        )


        new_email = st.text_input(
            "Email Address",
            key="signup_email"
        )


        phone = st.text_input(
            "Phone Number",
            key="signup_phone",
            placeholder="+923001234567"
        )


        st.markdown(
            "**Location / Address**"
        )


        col_prov, col_city = st.columns(2)


        with col_prov:

            selected_province = st.selectbox(
                "Province / Territory",
                options=list(
                    PAK_LOCATIONS.keys()
                ),
                key="signup_province"
            )


        with col_city:

            selected_city = st.selectbox(
                "City",
                options=PAK_LOCATIONS[
                    selected_province
                ],
                key="signup_city"
            )


        address = (
            f"{selected_city}, "
            f"{selected_province}, "
            f"Pakistan"
        )


        new_password = st.text_input(
            "Password",
            type="password",
            key="signup_pass"
        )


        if st.button(
            "Register",
            key="btn_signup",
            use_container_width=True
        ):

            if (
                not username
                or not new_email
                or not phone
                or not address
                or not new_password
            ):

                st.warning(
                    "Please fill in all required fields!"
                )


            elif len(new_password) < 6:

                st.warning(
                    "Password must be at least 6 characters long!"
                )


            else:

                try:

                    # ----------------------------------------
                    # CREATE SUPABASE ACCOUNT
                    # ----------------------------------------

                    auth_response = (
                        supabase.auth.sign_up(
                            {
                                "email": new_email,

                                "password": new_password,

                                "options": {
                                    "data": {

                                        "username": username,

                                        "phone": phone.strip(),

                                        "address": address,
                                    }
                                },
                            }
                        )
                    )


                    user_obj = auth_response.user


                    # ----------------------------------------
                    # CREATE PROFILE
                    # ----------------------------------------

                    if user_obj and supabase_admin:

                        profile_data = {

                            "id": user_obj.id,

                            "email": (
                                new_email
                                .strip()
                                .lower()
                            ),

                            "username": (
                                username
                                .strip()
                            ),

                            "phone": (
                                phone
                                .strip()
                            ),

                            "address": (
                                address
                                .strip()
                            )
                        }


                        (
                            supabase_admin
                            .table("profiles")
                            .upsert(profile_data)
                            .execute()
                        )


                        st.session_state[
                            "user_profile"
                        ] = profile_data


                    st.success(
                        "✅ Account created successfully! "
                        "Please switch to the Login tab to sign in."
                    )


                except Exception as e:

                    st.error(
                        f"❌ Registration failed: {e}"
                    )


    # ========================================================
    # FORGOT PASSWORD TAB
    # ========================================================

    with tab_forgot:

        st.subheader("🔑 Reset Password")


        # ====================================================
        # ACCOUNT VERIFICATION
        # ====================================================

        if not st.session_state["reset_verified"]:

            st.info(
                "💡 Enter your registered "
                "**Email Address** and "
                "**Phone Number** to verify your account."
            )


            reset_email = st.text_input(
                "Registered Email Address",
                key="reset_email_input"
            )


            reset_phone = st.text_input(
                "Registered Phone Number",
                key="reset_phone_input",
                placeholder="+923001234567"
            )


            if st.button(
                "🔍 Verify Account Details",
                key="btn_verify_account",
                use_container_width=True
            ):

                if (
                    not reset_email.strip()
                    or not reset_phone.strip()
                ):

                    st.warning(
                        "Please enter both Email Address "
                        "and Phone Number!"
                    )


                else:

                    with st.spinner(
                        "Checking database for matching account..."
                    ):

                        try:

                            res = (
                                supabase_admin
                                .table("profiles")
                                .select(
                                    "id, email, phone"
                                )
                                .eq(
                                    "email",
                                    reset_email
                                    .strip()
                                    .lower()
                                )
                                .eq(
                                    "phone",
                                    reset_phone.strip()
                                )
                                .execute()
                            )


                            if (
                                res.data
                                and len(res.data) > 0
                            ):

                                target_user = res.data[0]


                                st.session_state[
                                    "reset_verified"
                                ] = True


                                st.session_state[
                                    "reset_target_user_id"
                                ] = target_user["id"]


                                st.session_state[
                                    "reset_matched_email"
                                ] = target_user["email"]


                                st.success(
                                    "✅ Account verified successfully!"
                                )


                                st.rerun()


                            else:

                                st.error(
                                    "❌ Invalid credentials! "
                                    "No matching account found "
                                    "with this email and phone number."
                                )


                        except Exception as e:

                            st.error(
                                f"❌ Verification failed: {e}"
                            )


        # ====================================================
        # PASSWORD UPDATE
        # ====================================================

        else:

            st.success(
                f"✅ Verified Account: "
                f"**{st.session_state['reset_matched_email']}**"
            )


            st.subheader(
                "Set Your New Password"
            )


            pass_1 = st.text_input(
                "New Password",
                type="password",
                key="reset_new_pass"
            )


            pass_2 = st.text_input(
                "Confirm New Password",
                type="password",
                key="reset_conf_pass"
            )


            col1, col2 = st.columns([3, 1])


            # =================================================
            # UPDATE PASSWORD
            # =================================================

            with col1:

                if st.button(
                    "💾 Update Password",
                    key="btn_save_pass",
                    use_container_width=True
                ):

                    if not pass_1 or not pass_2:

                        st.warning(
                            "Please fill in both password fields!"
                        )


                    elif pass_1 != pass_2:

                        st.error(
                            "❌ Passwords do not match!"
                        )


                    elif len(pass_1) < 6:

                        st.warning(
                            "⚠️ Password must be at least "
                            "6 characters long."
                        )


                    else:

                        try:

                            with st.spinner(
                                "Updating password securely..."
                            ):

                                supabase_admin.auth.admin.update_user_by_id(
                                    st.session_state[
                                        "reset_target_user_id"
                                    ],
                                    {
                                        "password": pass_1
                                    },
                                )


                                # ----------------------------
                                # RESET STATE
                                # ----------------------------

                                st.session_state[
                                    "reset_verified"
                                ] = False


                                st.session_state[
                                    "reset_target_user_id"
                                ] = None


                                st.session_state[
                                    "reset_matched_email"
                                ] = ""


                                st.success(
                                    "🎉 Password updated successfully! "
                                    "Please switch to Login tab."
                                )


                        except Exception as e:

                            st.error(
                                f"❌ Failed to update password: {e}"
                            )


            # =================================================
            # GO BACK
            # =================================================

            with col2:

                if st.button(
                    "🔙 Go Back",
                    key="btn_back_reset",
                    use_container_width=True
                ):

                    st.session_state[
                        "reset_verified"
                    ] = False


                    st.session_state[
                        "reset_target_user_id"
                    ] = None


                    st.session_state[
                        "reset_matched_email"
                    ] = ""


                    st.rerun()
