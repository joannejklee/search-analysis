"""
Script 1: Text Analysis & Vocabulary Extraction
Analyzes inquiry_text, brand_name, and job_name fields to extract user vocabulary
"""

import sys
import subprocess
import os

# Check and install required packages
required_packages = {
    'pandas': 'pandas',
    'numpy': 'numpy',
    'plotly': 'plotly',
    'deep_translator': 'deep-translator',
    'langdetect': 'langdetect'
}

print("Checking required packages...")
for package, pip_name in required_packages.items():
    try:
        __import__(package)
        print(f"✓ {package} already installed")
    except ImportError:
        print(f"✗ {package} not found. Installing {pip_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--break-system-packages"])
        print(f"✓ {pip_name} installed successfully")

# Now import everything
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import re
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
import json

print("\n" + "="*80)
print("SCRIPT 1: TEXT ANALYSIS & VOCABULARY EXTRACTION")
print("="*80 + "\n")

# Configuration
DATA_DIR = "data"
OUTPUT_DIR = "outputs/vocabulary"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read data
print("Loading data...")
df = pd.read_csv(f"{DATA_DIR}/2025_Bookings.csv")
print(f"✓ Loaded {len(df)} bookings from {df['job_id'].nunique()} unique jobs\n")

# Deduplicate at job level for vocabulary analysis
print("Deduplicating at job level...")
job_df = df.drop_duplicates(subset='job_id', keep='first')
print(f"✓ {len(job_df)} unique jobs for vocabulary analysis\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def detect_language(text):
    """Detect if text is Korean or English"""
    if pd.isna(text) or str(text).strip() == '':
        return 'unknown'
    try:
        lang = detect(str(text))
        return 'korean' if lang == 'ko' else 'english' if lang == 'en' else 'other'
    except LangDetectException:
        return 'unknown'

def translate_text(text, src='ko', dest='en'):
    """Translate text using Google Translate via deep-translator"""
    if pd.isna(text) or str(text).strip() == '':
        return ''
    try:
        # deep-translator uses 'auto' for automatic detection
        translator = GoogleTranslator(source=src, target=dest)
        result = translator.translate(str(text))
        return result
    except Exception as e:
        print(f"Translation error: {e}")
        return str(text)

def clean_text(text):
    """Clean text for analysis"""
    if pd.isna(text):
        return ''
    text = str(text)
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    # Remove special characters but keep Korean, English, numbers, spaces
    text = re.sub(r'[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]', ' ', text)
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text

def extract_keywords(text, min_length=2):
    """Extract keywords from text"""
    if not text:
        return []
    words = text.split()
    # Filter out very short words and common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were',
                  '이', '그', '저', '것', '수', '등', '및', '를', '을', '가', '이', '에', '의'}
    keywords = [w for w in words if len(w) >= min_length and w.lower() not in stop_words]
    return keywords

def extract_phrases(text):
    """Extract 2-3 word phrases from text"""
    if pd.isna(text) or str(text).strip() == '':
        return []
    
    # Tokenize (keep Korean and English)
    tokens = re.findall(r'[\w가-힣]+', str(text))
    
    phrases = []
    # 2-word phrases
    for i in range(len(tokens) - 1):
        phrase = f"{tokens[i]} {tokens[i+1]}"
        if len(phrase) >= 4:  # Skip very short phrases
            phrases.append(phrase)
    
    # 3-word phrases
    for i in range(len(tokens) - 2):
        phrase = f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}"
        if len(phrase) >= 6:
            phrases.append(phrase)
    
    return phrases

# ============================================================================
# LANGUAGE DETECTION & TRANSLATION
# ============================================================================

print("Processing text fields...")
print("1. Detecting languages...")

# Detect languages
job_df['brand_name_lang'] = job_df['brand_name'].apply(detect_language)
job_df['job_name_lang'] = job_df['job_name'].apply(detect_language)
job_df['inquiry_text_lang'] = job_df['inquiry_text'].apply(detect_language)

print("2. Translating Korean text to English...")
# Translate Korean to English
job_df['brand_name_en'] = job_df.apply(
    lambda row: translate_text(row['brand_name'], 'ko', 'en') 
    if row['brand_name_lang'] == 'korean' else row['brand_name'], axis=1
)

job_df['job_name_en'] = job_df.apply(
    lambda row: translate_text(row['job_name'], 'ko', 'en') 
    if row['job_name_lang'] == 'korean' else row['job_name'], axis=1
)

job_df['inquiry_text_en'] = job_df.apply(
    lambda row: translate_text(row['inquiry_text'], 'ko', 'en') 
    if row['inquiry_text_lang'] == 'korean' else row['inquiry_text'], axis=1
)

print("✓ Translation complete\n")

# ============================================================================
# TEXT CLEANING & KEYWORD EXTRACTION
# ============================================================================

print("3. Cleaning text and extracting keywords...")

# Clean text
job_df['brand_name_clean'] = job_df['brand_name'].apply(clean_text)
job_df['job_name_clean'] = job_df['job_name'].apply(clean_text)
job_df['inquiry_text_clean'] = job_df['inquiry_text'].apply(clean_text)
job_df['inquiry_text_en_clean'] = job_df['inquiry_text_en'].apply(clean_text)

# Extract keywords and phrases
job_df['inquiry_keywords'] = job_df['inquiry_text_clean'].apply(extract_keywords)
job_df['inquiry_phrases'] = job_df['inquiry_text_clean'].apply(extract_phrases)

print("✓ Text processing complete\n")

# ============================================================================
# VOCABULARY ANALYSIS
# ============================================================================

print("="*80)
print("ANALYZING VOCABULARY")
print("="*80 + "\n")

# 1. Job Names / Project Types
print("1. JOB NAMES / PROJECT TYPES")
print("-" * 40)
job_names = job_df['job_name_clean'].value_counts().head(20)
print(f"Top 20 most common job names:")
for job, count in job_names.items():
    print(f"  {job}: {count}")
print()

# 2. Inquiry Text Phrases
print("2. INQUIRY TEXT PHRASES")
print("-" * 40)

# Get all phrases from inquiry texts
all_phrases = []
for phrases in job_df['inquiry_phrases']:
    all_phrases.extend(phrases)

phrase_freq = Counter(all_phrases)
top_phrases = phrase_freq.most_common(50)

print(f"Top 50 phrases from inquiry texts:")
for phrase, count in top_phrases:
    print(f"  {phrase}: {count}")
print()

# 3. Translating Top Phrases and Job Names
print("3. TRANSLATING TOP PHRASES AND JOB NAMES")
print("-" * 40)

# Translate top 30 phrases
top_30_phrases = phrase_freq.most_common(30)
phrase_translations = {}
print(f"Translating top 30 phrases...")
for idx, (phrase, count) in enumerate(top_30_phrases, 1):
    translation = translate_text(phrase, 'ko', 'en')
    phrase_translations[phrase] = translation
    if idx % 5 == 0:
        print(f"  Progress: {idx}/30 phrases translated")

# Translate top 20 job names
job_name_translations = {}
print(f"\nTranslating top 20 job names...")
for idx, job_name in enumerate(job_names.head(20).index, 1):
    translation = translate_text(job_name, 'ko', 'en')
    job_name_translations[job_name] = translation
    if idx % 5 == 0:
        print(f"  Progress: {idx}/20 job names translated")

print("✓ All translations complete\n")

# Analyze English translations for concept words
print("4. CONCEPT-RELATED VOCABULARY (from English translations)")
print("-" * 40)

concept_words = ['concept', 'style', 'vibe', 'mood', 'theme', 'feel', 'aesthetic',
                 'casual', 'formal', 'minimal', 'modern', 'vintage', 'natural',
                 'professional', 'lifestyle', 'commercial', 'editorial']

concept_mentions = {}
for word in concept_words:
    count = job_df['inquiry_text_en_clean'].str.lower().str.contains(word, na=False).sum()
    if count > 0:
        concept_mentions[word] = count

concept_sorted = sorted(concept_mentions.items(), key=lambda x: x[1], reverse=True)
print("Concept-related words mentioned:")
for word, count in concept_sorted:
    print(f"  {word}: {count}")
print()

# ============================================================================
# VISUALIZATION
# ============================================================================

print("="*80)
print("GENERATING VISUALIZATIONS")
print("="*80 + "\n")

# 1. Top Phrases Bar Chart
print("1. Generating phrase frequency chart...")
phrases, counts = zip(*top_30_phrases)

fig = go.Figure(data=[
    go.Bar(x=list(counts), y=list(phrases), orientation='h',
           marker_color='steelblue')
])
fig.update_layout(
    title='Top 30 Most Frequent Phrases in Inquiry Text',
    xaxis_title='Frequency',
    yaxis_title='Phrase',
    height=800,
    yaxis={'categoryorder': 'total ascending'}
)
fig.write_html(f'{OUTPUT_DIR}/phrase_frequency.html')
print(f"✓ Saved: {OUTPUT_DIR}/phrase_frequency.html")

# 2. Language Distribution
print("2. Generating language distribution chart...")
lang_dist = job_df['inquiry_text_lang'].value_counts()
fig = go.Figure(data=[
    go.Pie(labels=lang_dist.index, values=lang_dist.values,
           hole=0.3)
])
fig.update_layout(title='Language Distribution in Inquiry Texts')
fig.write_html(f'{OUTPUT_DIR}/language_distribution.html')
print(f"✓ Saved: {OUTPUT_DIR}/language_distribution.html")

# ============================================================================
# EXPORT DATA
# ============================================================================

print("\n" + "="*80)
print("EXPORTING DATA")
print("="*80 + "\n")

# 1. Full vocabulary table with translations
vocab_export = job_df[[
    'job_id', 'brand_name', 'brand_name_lang', 'brand_name_en',
    'job_name', 'job_name_lang', 'job_name_en',
    'inquiry_text', 'inquiry_text_lang', 'inquiry_text_en'
]].copy()

vocab_export.to_csv(f'{OUTPUT_DIR}/vocabulary_with_translations.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/vocabulary_with_translations.csv")

# 2. Phrase frequency table with translations
phrase_df = pd.DataFrame({
    'Phrase (Korean)': [p for p, c in top_30_phrases],
    'English Translation': [phrase_translations[p] for p, c in top_30_phrases],
    'Frequency': [c for p, c in top_30_phrases]
})
phrase_df.to_csv(f'{OUTPUT_DIR}/phrase_frequency.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/phrase_frequency.csv")

# 3. Job name frequency table with translations
job_name_df = pd.DataFrame({
    'Job Name (Korean)': job_names.head(20).index,
    'English Translation': [job_name_translations[j] for j in job_names.head(20).index],
    'Frequency': job_names.head(20).values
})
job_name_df.to_csv(f'{OUTPUT_DIR}/job_name_frequency.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/job_name_frequency.csv")

# 5. Concept words frequency
concept_df = pd.DataFrame(concept_sorted, columns=['Concept Word', 'Frequency'])
concept_df.to_csv(f'{OUTPUT_DIR}/concept_words_frequency.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/concept_words_frequency.csv")

# ============================================================================
# GENERATE HTML REPORT
# ============================================================================

print("\n" + "="*80)
print("GENERATING HTML REPORT")
print("="*80 + "\n")

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Text & Vocabulary Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        h1 {{
            margin: 0;
            font-size: 32px;
        }}
        .subtitle {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        .section {{
            background: white;
            padding: 30px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #667eea;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .translation {{
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Text & Vocabulary Analysis Report</h1>
        <div class="subtitle">Analysis of job names and inquiry phrases from 2025 bookings</div>
    </div>

    <div class="section">
        <h2>📈 Overview Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{len(job_df)}</div>
                <div class="stat-label">Unique Jobs</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(df)}</div>
                <div class="stat-label">Total Bookings</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(phrase_freq)}</div>
                <div class="stat-label">Unique Phrases</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{job_df['inquiry_text_lang'].value_counts().get('korean', 0)}</div>
                <div class="stat-label">Korean Texts</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>📝 Top 20 Job Names</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Job Name (Korean)</th>
                    <th>English Translation</th>
                    <th>Frequency</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{i+1}</td><td>{job}</td><td class='translation'>{job_name_translations.get(job, '')}</td><td>{count}</td></tr>" 
                          for i, (job, count) in enumerate(job_names.head(20).items())])}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🔑 Top 30 Phrases from Inquiry Text</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Phrase (Korean)</th>
                    <th>English Translation</th>
                    <th>Frequency</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{i+1}</td><td>{phrase}</td><td class='translation'>{phrase_translations.get(phrase, '')}</td><td>{count}</td></tr>" 
                          for i, (phrase, count) in enumerate(top_30_phrases)])}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🎨 Concept-Related Vocabulary</h2>
        <table>
            <thead>
                <tr>
                    <th>Concept Word</th>
                    <th>Frequency</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{word}</td><td>{count}</td></tr>" 
                          for word, count in concept_sorted])}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>📁 Exported Files</h2>
        <ul>
            <li><strong>vocabulary_with_translations.csv</strong> - Full dataset with translations</li>
            <li><strong>phrase_frequency.csv</strong> - Top 30 phrases with English translations</li>
            <li><strong>job_name_frequency.csv</strong> - Top 20 job names with English translations</li>
            <li><strong>concept_words_frequency.csv</strong> - Concept-related word frequencies</li>
        </ul>
    </div>
</body>
</html>
"""

with open(f'{OUTPUT_DIR}/vocabulary_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Saved: {OUTPUT_DIR}/vocabulary_report.html")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ SCRIPT 1 COMPLETE!")
print("="*80 + "\n")

print("📊 Summary:")
print(f"  • Analyzed {len(job_df)} unique jobs")
print(f"  • Extracted {len(phrase_freq)} unique phrases")
print(f"  • Translated {job_df['inquiry_text_lang'].value_counts().get('korean', 0)} Korean texts")
print(f"  • Translated top 30 phrases and top 20 job names to English")
print(f"  • Generated {len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(('.html', '.csv'))])} output files")
print(f"\n📁 All outputs saved to: {OUTPUT_DIR}/")
print(f"\n🌐 Open 'vocabulary_report.html' in your browser to view the interactive report!")
print("\n" + "="*80 + "\n")
