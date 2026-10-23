// Language context for English & Tamil (தமிழ்) localization
import React, { createContext, useContext, useState, useEffect } from 'react';

const REASON_TRANSLATIONS = {
  // Common backend reason strings mapped to Tamil
  "New recipient": "புதிய பெறுநர் (முதல் முறை பரிவர்த்தனை)",
  "Amount is unusually high": "தொகை வழக்கத்திற்கு மாறாக அதிகமாக உள்ளது",
  "Unfamiliar device": "அறியப்படாத அல்லது மாற்றப்பட்ட சாதனம்",
  "New beneficiary: No prior financial history with this VPA": "புதிய பெறுநர்: இந்த UPI கணக்குடன் முன் பரிவர்த்தனை வரலாறு இல்லை",
  "Unverified merchant / individual handle": "சரிபார்க்கப்படாத வணிகர் அல்லது தனிநபர் கணக்கு",
  "Flagged Mule Ring: Known high-velocity aggregation node (I4C Match)": "மியூல் கணக்கு எச்சரிக்கை: தேசிய சைபர் குற்றப்பிரிவு (I4C) தரவுத்தளத்தில் கண்டறியப்பட்டது",
  "Unusual pass-through pattern detected in recipient cluster": "பெறுநர் கணக்கில் அசாதாரண துரித பண விநியோகம் கண்டறியப்பட்டது",
  "Mule account identifier signature matched in National Registry": "தேசிய மியூல் கணக்கு பதிவேட்டில் அடையாளம் பொருந்தியது",
  "Multiple recent cyber fraud complaints associated with beneficiary": "பெறுநர் மீது பல அண்மைய சைபர் மோசடி புகார்கள் பதிவாகியுள்ளன",
  "Amount exceeds daily single-transaction high-risk threshold (₹50,000+)": "தொகை அனுமதிக்கப்பட்ட ஒருமுறை உச்சவரம்பை (₹50,000+) விட அதிகம்",
  "Velocity anomaly: First-time outsized payment": "திடீர் உச்ச தொகை பரிவர்த்தனை முரண்பாடு",
  "High transaction value relative to user standard profile": "பயனரின் வழக்கமான பரிவர்த்தனை தொகையை விட கணிசமாக அதிகம்",
  "Payment requires secondary authentication confirmation": "பரிவர்த்தனைக்கு கூடுதல் உறுதிப்படுத்தல் தேவைப்படுகிறது",
  "Legitimate recipient profile & normal velocity match": "சரிபார்க்கப்பட்ட முறையான பெறுநர் & இயல்பான வேகம்",
  "Within standard peer-to-peer risk tolerance": "வழக்கமான நுகர்வோர் பாதுகாப்பு வரம்பிற்குள் உள்ளது",
  "Unfamiliar device or altered SIM binding detected": "அறியப்படாத சாதனம் அல்லது புதிய சிம் கார்டு கண்டறியப்பட்டது",
  "Verified family contact": "சரிபார்க்கப்பட்ட குடும்ப உறுப்பினர் தொடர்பு",
  "Consistent transaction history": "சீரான நம்பகமான பரிவர்த்தனை வரலாறு",
  "Trusted device signature": "நம்பகமான பதிவுசெய்யப்பட்ட சாதனம்",
  "First time transacting with this VPA": "இந்த UPI முகவரியுடன் முதல் முறை பரிவர்த்தனை",
  "Recipient handle registered < 48 hours ago": "பெறுநர் UPI முகவரி 48 மணி நேரத்திற்குள் உருவாக்கப்பட்டது",
  "Slight deviation from normal spending pattern": "வழக்கமான செலவு முறையில் சிறிய மாற்றம்",
  "Monthly recurring pattern matched": "மாதாந்திர வழக்கமான வாடகை/கட்டண முறை பொருந்தியது",
  "Beneficiary verified > 6 months": "6 மாதங்களுக்கும் மேலாக சரிபார்க்கப்பட்ட பயனாளி",
  "Keywords match known social engineering lottery phishing scam": "லாட்டரி/பரிசு தொடர்பான மோசடி சொற்கள் கண்டறியப்பட்டன",
  "Recipient VPA has 14 prior fraud reports this week": "பெறுநர் முகவரிக்கு இந்த வாரம் 14 மோசடி புகார்கள் உள்ளன",
  "Mule account cluster connection detected": "மியூல் கணக்கு வலையமைப்பு இணைப்பு கண்டறியப்பட்டது",
  "Verified merchant QR": "சரிபார்க்கப்பட்ட வணிகர் க்யூஆர் குறியீடு",
  "Trusted terminal": "நம்பகமான விற்பனை முனையம்",
  "High amount to newly created merchant account": "புதிதாக உருவாக்கப்பட்ட வணிகர் கணக்கிற்கு அதிக தொகை",
  "Absence of historical reciprocal transactions": "முந்தைய இருவழி பரிவர்த்தனைகள் இல்லை",
  "Off-peak transaction hour": "வழக்கத்திற்கு மாறான நள்ளிரவு நேரம்"
};

const TRANSLATIONS = {
  en: {
    app_title: "UPI Shield AI",
    app_subtitle: "Real-Time UPI Fraud Detection & Mule Account Intelligence",
    hackathon_track: "VIT College • Track 4: FinTech & GovTech Intelligence",
    
    // Navigation
    nav_simulator: "Payment Simulator",
    nav_transactions: "Transaction Feed",
    nav_dashboard: "Analyst Dashboard",
    nav_network: "Mule Network",
    nav_cases: "Case Management",
    
    // Status
    status_connected: "FastAPI Connected",
    status_offline: "Backend Offline (Demo Fallback)",
    status_checking: "Checking Backend...",
    
    // Decisions
    decision_allow: "ALLOW",
    decision_warn: "WARN",
    decision_hold: "HOLD",
    
    // Simulator Form
    sim_title: "Instant UPI Transfer Simulator",
    sim_badge_sub: "Zero-Latency Fraud Intelligence",
    sim_sender_label: "Debit From (Sender Account)",
    sim_balance: "Available Balance",
    sim_recipient_label: "Pay To (Recipient UPI ID / VPA)",
    sim_recipient_name: "Recipient Name",
    sim_amount_label: "Amount (INR ₹)",
    sim_note_label: "Add a note (optional)",
    sim_note_placeholder: "e.g., Dinner, Tuition, Electronics",
    sim_quick_presets: "Quick Presets & Test Scenarios",
    sim_preset_known: "Known Safe",
    sim_preset_new: "New Recipient",
    sim_preset_mule: "Suspicious Mule",
    sim_device_toggle: "Simulate Device Change / SIM Swap Telemetry",
    sim_device_desc: "Triggers biometric & device fingerprint deviation in ML pipeline",
    sim_btn_analyze_pay: "Analyze & Pay Securely",
    sim_btn_analyzing: "Scoring with AI Pipeline...",
    sim_disclaimer: "Academic Simulation: No real bank account debited. Protected by UPI Shield AI Engine.",
    
    // Flow Stages
    stage_fingerprint: "Validating Device & SIM Hardware Fingerprint...",
    stage_velocity: "Computing Ingress Velocity & Graph Outlier Score...",
    stage_mule_check: "Querying National Mule Account Intelligence Graph...",
    stage_ml_eval: "Synthesizing Gradient-Boosted Risk Classifier...",
    
    // Decision Outcomes
    outcome_allow_title: "Transaction Approved & Completed",
    outcome_allow_msg: "Risk assessment passed. Transaction verified against known safe patterns.",
    outcome_warn_title: "Security Caution: Suspicious Indicators Detected",
    outcome_warn_msg: "Our AI model flagged anomalies. Please review the risk reasons carefully before confirming.",
    outcome_hold_title: "Transaction Blocked: Put On Security Hold",
    outcome_hold_msg: "Critical fraud risk detected. Funds held to protect your account. No money has left your bank.",
    
    // Buttons
    btn_proceed_anyway: "I Understand the Risks, Proceed Anyway",
    btn_cancel_tx: "Cancel Transaction & Report",
    btn_make_another: "Simulate Another Payment",
    btn_view_history: "View in Audit Log",
    btn_view_network: "Inspect in Mule Network",
    btn_report_cyber: "Escalate to Cyber Crime 1930 / I4C",
    
    // Fallback indicator
    fallback_badge: "DEMO FALLBACK - BACKEND OFFLINE",
    fallback_expl: "Heuristic rule preview. Connect Python FastAPI backend for live XGBoost/IsolationForest model predictions.",
    
    // Receipt
    receipt_title: "UPI Payment Receipt",
    receipt_status_success: "PAID SUCCESSFULLY",
    receipt_utr: "Bank Reference (UTR)",
    receipt_tx_id: "Shield Transaction ID",
    receipt_date: "Date & Time",
    receipt_mode: "Payment Mode",
    receipt_risk_cleared: "Risk Cleared",
    
    // History
    history_title: "UPI Transaction Audit Feed",
    history_subtitle: "Real-time stream of evaluated peer-to-peer and merchant transfers",
    history_filter_all: "All Decisions",
    history_search_placeholder: "Search by UTR, VPA, Sender, or Tx ID...",
    history_export_csv: "Export CSV Log",
    history_empty: "No transactions found matching the selected criteria.",
    
    // Dashboard
    dash_title: "Fraud Analyst Intelligence Console",
    dash_subtitle: "Live surveillance, mule rings & suspicious flow interception",
    dash_total_vol: "Evaluated Volume",
    dash_flagged_warns: "Friction Warns",
    dash_holds: "Blocked Holds",
    dash_active_alerts: "Active Alerts",
    dash_avg_latency: "Inference Latency",
    dash_mule_intercepted: "Mule Accounts Intercepted",
    
    // Network
    net_title: "Mule Account Intelligence Graph",
    net_subtitle: "Graph-theoretic anomaly visualization of multi-hop fund layering",
    net_select_scenario: "Select Investigation Scenario",
    net_legend_victim: "Victim Account",
    net_legend_tier1: "Tier-1 Mule",
    net_legend_hub: "Layering Aggregator Hub",
    net_legend_offramp: "Exfiltration / Off-ramp",
    net_btn_freeze: "Freeze VPA in Sandbox",
    net_btn_escalate: "File I4C Intelligence Dossier",
    
    // Cases
    case_title: "Case Management & Cyber Cell Dossiers",
    case_subtitle: "GovTech & Bank FIU coordination queue for mule ring disruption",
    case_filter_all: "All Cases",
    case_filter_open: "Open",
    case_filter_investigating: "Under Investigation",
    case_filter_closed: "Closed",
    case_update_status: "Update Status",
    case_action_frozen: "Lien Placed & Account Frozen",
    case_add_note: "Add Analyst Investigation Note",
    
    // General
    risk_score: "Risk Score",
    scoring_latency: "Inference Latency",
    detected_reasons: "AI Detected Risk Factors",
    investigate: "Investigate",
    details: "Details"
  },
  ta: {
    app_title: "UPI ஷீல்ட் AI",
    app_subtitle: "நிகழ்நேர UPI மோசடி தடுப்பு மற்றும் மியூல் கணக்கு நுண்ணறிவு",
    hackathon_track: "VIT கல்லூரி • தடம் 4: ஃபின்டெக் & அரசு தொழில்நுட்ப நுண்ணறிவு",
    
    // Navigation
    nav_simulator: "பரிவர்த்தனை மாதிரி",
    nav_transactions: "பரிவர்த்தனை பதிவுகள்",
    nav_dashboard: "மோசடி கட்டுப்பாட்டு அறை",
    nav_network: "மியூல் கணக்கு வலையமைப்பு",
    nav_cases: "வழக்கு மேலாண்மை",
    
    // Status
    status_connected: "FastAPI இணைக்கப்பட்டுள்ளது",
    status_offline: "பின்னணி ஆஃப்லைனில் உள்ளது (மாதிரி முறை)",
    status_checking: "இணைப்பு சோதிக்கப்படுகிறது...",
    
    // Decisions
    decision_allow: "அனுமதி (ALLOW)",
    decision_warn: "எச்சரிக்கை (WARN)",
    decision_hold: "நிறுத்திவைப்பு (HOLD)",
    
    // Simulator Form
    sim_title: "UPI பணப் பரிவர்த்தனை மாதிரி",
    sim_badge_sub: "பூஜ்ஜிய-தாமத மோசடி நுண்ணறிவு",
    sim_sender_label: "பணம் செலுத்தும் கணக்கு (அனுப்புநர்)",
    sim_balance: "இருப்புத் தொகை",
    sim_recipient_label: "பெறுநர் UPI முகவரி (VPA)",
    sim_recipient_name: "பெறுநர் பெயர்",
    sim_amount_label: "பரிவர்த்தனை தொகை (ரூபாய் ₹)",
    sim_note_label: "குறிப்பு (விரும்பினால்)",
    sim_note_placeholder: "எ.கா: வாடகை, மளிகை, கட்டணம்",
    sim_quick_presets: "பரிசோதனை மாதிரிகள்",
    sim_preset_known: "நம்பகமான நபர்",
    sim_preset_new: "புதிய பெறுநர்",
    sim_preset_mule: "சந்தேகத்திற்குரிய கணக்கு",
    sim_device_toggle: "சாதன மாற்றம் / சிம் கார்டு மாற்றத்தை சோதிக்கவும்",
    sim_device_desc: "AI மாதிரியில் பயோமெட்ரிக் மற்றும் சாதன விலகலைத் தூண்டுகிறது",
    sim_btn_analyze_pay: "ஆய்வு செய்து பாதுகாப்பாக செலுத்துக",
    sim_btn_analyzing: "AI மூலம் இடர் கணிக்கப்படுகிறது...",
    sim_disclaimer: "கல்வி சார்ந்த மாதிரி மட்டுமே: வங்கிக் கணக்கிலிருந்து உண்மையான பணம் கழிக்கப்படாது.",
    
    // Flow Stages
    stage_fingerprint: "சாதனம் மற்றும் சிம் வன்பொருள் சரிபார்க்கப்படுகிறது...",
    stage_velocity: "பணப் பரிமாற்ற வேகம் மற்றும் முரண்பாடுகள் கணக்கிடப்படுகின்றன...",
    stage_mule_check: "தேசிய மியூல் கணக்கு வரைபடத்தில் தேடப்படுகிறது...",
    stage_ml_eval: "AI இடர் மாதிரி இறுதி முடிவை உருவாக்குகிறது...",
    
    // Decision Outcomes
    outcome_allow_title: "பரிவர்த்தனை வெற்றிகரமாக அங்கீகரிக்கப்பட்டது",
    outcome_allow_msg: "பாதுகாப்பு சோதனை நிறைவடைந்தது. இந்த பரிவர்த்தனையில் எந்த இடரும் கண்டறியப்படவில்லை.",
    outcome_warn_title: "பாதுகாப்பு எச்சரிக்கை: சந்தேகத்திற்குரிய அறிகுறிகள்",
    outcome_warn_msg: "எங்கள் AI மாதிரி சில அசாதாரண அறிகுறிகளைக் கண்டறிந்துள்ளது. உறுதிப்படுத்தும் முன் காரணங்களை கவனமாகப் பார்க்கவும்.",
    outcome_hold_title: "பரிவர்த்தனை தடுக்கப்பட்டது: தற்காலிக நிறுத்திவைப்பு",
    outcome_hold_msg: "முக்கிய மோசடி ஆபத்து கண்டறியப்பட்டது. உங்கள் கணக்கை பாதுகாக்க பணம் நிறுத்தப்பட்டுள்ளது. பணம் எடுக்கப்படவில்லை.",
    
    // Buttons
    btn_proceed_anyway: "நான் ஆபத்தை உணர்கிறேன், பரிவர்த்தனையை தொடரவும்",
    btn_cancel_tx: "பரிவர்த்தனையை ரத்து செய்து புகாரளி",
    btn_make_another: "மற்றொரு பரிவர்த்தனையை சோதிக்கவும்",
    btn_view_history: "பதிவுகளில் பார்க்கவும்",
    btn_view_network: "வலையமைப்பில் ஆராய்க",
    btn_report_cyber: "சைபர் கிரைம் 1930 / I4C-ல் புகாரளி",
    
    // Fallback indicator
    fallback_badge: "டெமோ மாதிரி - பின்னணி ஆஃப்லைனில் உள்ளது",
    fallback_expl: "இது உத்தேச விதிமுறை முன்னோட்டம் மட்டுமே. உண்மையான ML கணிப்புகளுக்கு Python FastAPI பின்னணியை இணைக்கவும்.",
    
    // Receipt
    receipt_title: "UPI கட்டண ரசீது",
    receipt_status_success: "பணம் வெற்றிகரமாக செலுத்தப்பட்டது",
    receipt_utr: "வங்கி குறிப்பு எண் (UTR)",
    receipt_tx_id: "ஷீல்ட் பரிவர்த்தனை எண்",
    receipt_date: "தேதி மற்றும் நேரம்",
    receipt_mode: "கட்டண முறை",
    receipt_risk_cleared: "இடர் சோதனை: தேர்ச்சி",
    
    // History
    history_title: "UPI பரிவர்த்தனை தணிக்கைப் பதிவு",
    history_subtitle: "மதிப்பீடு செய்யப்பட்ட அனைத்து UPI பரிவர்த்தனைகளின் நேரடி பட்டியல்",
    history_filter_all: "அனைத்து முடிவுகளும்",
    history_search_placeholder: "UTR, UPI முகவரி, பெயர் மூலம் தேடவும்...",
    history_export_csv: "CSV தரவிறக்கம்",
    history_empty: "தேர்ந்தெடுக்கப்பட்ட நிபந்தனைகளுக்கு எந்த பரிவர்த்தனைகளும் இல்லை.",
    
    // Dashboard
    dash_title: "மோசடி ஆய்வாளர் கட்டுப்பாட்டு அறை",
    dash_subtitle: "நேரடி கண்காணிப்பு, மியூல் வலையமைப்புகள் மற்றும் மோசடி முடக்கம்",
    dash_total_vol: "ஆய்வு செய்யப்பட்ட மொத்த தொகை",
    dash_flagged_warns: "எச்சரிக்கை செய்யப்பட்டவை",
    dash_holds: "முடக்கப்பட்டவை",
    dash_active_alerts: "செயலில் உள்ள எச்சரிக்கைகள்",
    dash_avg_latency: "AI மதிப்பீட்டு தாமதம்",
    dash_mule_intercepted: "முடக்கப்பட்ட மியூல் கணக்குகள்",
    
    // Network
    net_title: "மியூல் கணக்கு நுண்ணறிவு வரைபடம்",
    net_subtitle: "பணப் பரிமாற்ற சுழற்சி மற்றும் அடுக்கு முறைகளின் ஊடாடும் வரைபடம்",
    net_select_scenario: "விசாரணை காட்சியைத் தேர்ந்தெடுக்கவும்",
    net_legend_victim: "பாதிக்கப்பட்ட கணக்கு",
    net_legend_tier1: "நிலை-1 மியூல் கணக்கு",
    net_legend_hub: "பணக் குவிப்பு மையம்",
    net_legend_offramp: "வெளியேற்றும் தளம்",
    net_btn_freeze: "கணக்கை முடக்கு (Sandbox)",
    net_btn_escalate: "I4C புலனாய்வு கோப்பை அனுப்பு",
    
    // Cases
    case_title: "வழக்கு மேலாண்மை மற்றும் சைபர் பிரிவு கோப்புகள்",
    case_subtitle: "மியூல் வலையமைப்பை முறியடிக்கும் வங்கி & அரசு புலனாய்வு வரிசை",
    case_filter_all: "அனைத்து வழக்குகள்",
    case_filter_open: "திறந்த வழக்குகள்",
    case_filter_investigating: "விசாரணையில் உள்ளவை",
    case_filter_closed: "நிறைவு செய்யப்பட்டவை",
    case_update_status: "நிலையை மாற்று",
    case_action_frozen: "கணக்கு முடக்கப்பட்டு பற்று நிறுத்தப்பட்டது",
    case_add_note: "ஆய்வாளர் குறிப்பைச் சேர்க்க",
    
    // General
    risk_score: "இடர் மதிப்பீடு",
    scoring_latency: "மதிப்பீட்டு நேரம்",
    detected_reasons: "AI கண்டறிந்த இடர் காரணிகள்",
    investigate: "ஆராய்க",
    details: "விவரங்கள்"
  }
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('en');

  // Load saved preference if any
  useEffect(() => {
    const saved = localStorage.getItem('upishield_lang');
    if (saved === 'en' || saved === 'ta') {
      setLang(saved);
    }
  }, []);

  const toggleLanguage = () => {
    const next = lang === 'en' ? 'ta' : 'en';
    setLang(next);
    localStorage.setItem('upishield_lang', next);
  };

  const t = (key) => {
    return TRANSLATIONS[lang]?.[key] || TRANSLATIONS.en[key] || key;
  };

  /**
   * Helper to translate risk reason
   * If Tamil is selected, looks up the exact or fuzzy phrase, otherwise returns original
   */
  const translateReason = (reason) => {
    if (lang === 'en') return reason;
    if (REASON_TRANSLATIONS[reason]) return REASON_TRANSLATIONS[reason];
    
    // Check if substring matches
    for (const [key, val] of Object.entries(REASON_TRANSLATIONS)) {
      if (reason.toLowerCase().includes(key.toLowerCase())) {
        return val;
      }
    }
    return reason;
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, toggleLanguage, t, translateReason }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
