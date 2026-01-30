"""
Script 4: VOC Thematic Analysis
Analyzes customer feedback to extract themes and priorities using NLP
"""

import sys
import subprocess
import os

# Check and install required packages
required_packages = {
    'pandas': 'pandas',
    'numpy': 'numpy',
    'plotly': 'plotly',
    'sklearn': 'scikit-learn',
    'wordcloud': 'wordcloud',
    'matplotlib': 'matplotlib'
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
from plotly.subplots import make_subplots
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re
import json

print("\n" + "="*80)
print("SCRIPT 4: VOC THEMATIC ANALYSIS")
print("="*80 + "\n")

# Configuration
DATA_DIR = "data"
OUTPUT_DIR = "outputs/voc_analysis"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read data
print("Loading VOC data...")
df = pd.read_csv(f"{DATA_DIR}/VOC_Search.csv")
print(f"✓ Loaded {len(df)} VOC entries\n")

# ============================================================================
# DATA PREPROCESSING
# ============================================================================

print("Preprocessing data...")

# Use English text for NLP analysis
df['text'] = df['ENG'].fillna('')
df['text_clean'] = df['text'].str.lower()

# Remove very short entries
df = df[df['text'].str.len() > 20].copy()

print(f"✓ {len(df)} entries after filtering\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_text_for_analysis(text):
    """Clean text for analysis"""
    if not text:
        return ""
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', str(text))
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.lower()

def extract_keywords(text, n=10):
    """Extract top keywords from text"""
    words = text.split()
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
                  'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'can', 'may', 'might', 'must', 'i', 'you', 'we',
                  'they', 'it', 'this', 'that', 'these', 'those'}
    keywords = [w for w in words if len(w) > 3 and w not in stop_words]
    return Counter(keywords).most_common(n)

# ============================================================================
# CATEGORY ANALYSIS
# ============================================================================

print("="*80)
print("ANALYZING CATEGORIES")
print("="*80 + "\n")

# 1. Main Categories
print("1. MAIN CATEGORIES")
print("-" * 40)
category_dist = df['Categories'].value_counts()
print("Distribution:")
for cat, count in category_dist.items():
    pct = (count / len(df)) * 100
    print(f"  {cat}: {count} ({pct:.1f}%)")
print()

# 2. User Types
print("2. USER TYPES")
print("-" * 40)
user_type_dist = df['User Type'].value_counts()
print("Distribution:")
for utype, count in user_type_dist.items():
    pct = (count / len(df)) * 100
    print(f"  {utype}: {count} ({pct:.1f}%)")
print()

# 3. SubCategories
print("3. SUB-CATEGORIES")
print("-" * 40)
subcat_dist = df['SubCategories'].value_counts().head(10)
print("Top 10 subcategories:")
for subcat, count in subcat_dist.items():
    pct = (count / len(df)) * 100
    print(f"  {subcat}: {count} ({pct:.1f}%)")
print()

# ============================================================================
# KEYWORD EXTRACTION
# ============================================================================

print("="*80)
print("EXTRACTING KEYWORDS")
print("="*80 + "\n")

# Get all text combined
all_text = ' '.join(df['text_clean'])
all_keywords = extract_keywords(all_text, 50)

print("Top 50 keywords from VOC:")
for keyword, count in all_keywords:
    print(f"  {keyword}: {count}")
print()

# ============================================================================
# THEME IDENTIFICATION (Topic Modeling)
# ============================================================================

print("="*80)
print("IDENTIFYING THEMES (Topic Modeling)")
print("="*80 + "\n")

# Prepare text for topic modeling
texts = df['text_clean'].tolist()

# TF-IDF Vectorization
print("Running TF-IDF vectorization...")
tfidf_vectorizer = TfidfVectorizer(
    max_features=100,
    stop_words='english',
    min_df=2,
    max_df=0.8
)
tfidf_matrix = tfidf_vectorizer.fit_transform(texts)
feature_names = tfidf_vectorizer.get_feature_names_out()

# Topic Modeling with LDA
print("Running LDA topic modeling...")
n_topics = 5
lda = LatentDirichletAllocation(
    n_components=n_topics,
    random_state=42,
    max_iter=20
)
lda_topics = lda.fit_transform(tfidf_matrix)

# Extract top words per topic
def get_top_words(model, feature_names, n_words=10):
    topics = []
    for topic_idx, topic in enumerate(model.components_):
        top_indices = topic.argsort()[-n_words:][::-1]
        top_words = [feature_names[i] for i in top_indices]
        topics.append(top_words)
    return topics

lda_topics_words = get_top_words(lda, feature_names, 10)

print(f"\nIdentified {n_topics} main themes:")
print("-" * 40)
for i, words in enumerate(lda_topics_words, 1):
    print(f"\nTheme {i}: {', '.join(words[:5])}")
    print(f"  Keywords: {', '.join(words)}")

# Assign documents to themes
df['primary_theme'] = lda_topics.argmax(axis=1) + 1
df['theme_confidence'] = lda_topics.max(axis=1)

theme_dist = df['primary_theme'].value_counts().sort_index()
print("\nTheme distribution:")
for theme, count in theme_dist.items():
    pct = (count / len(df)) * 100
    print(f"  Theme {theme}: {count} entries ({pct:.1f}%)")
print()

# ============================================================================
# SENTIMENT & PRIORITY ANALYSIS
# ============================================================================

print("="*80)
print("ANALYZING PRIORITIES")
print("="*80 + "\n")

# Define priority keywords/phrases
priority_keywords = {
    'Search & Filter': ['search', 'filter', 'find', 'discovery', 'browse', 'nationality', 'race', 'ethnicity'],
    'Communication': ['chat', 'message', 'communication', 'response', 'reply', 'translation'],
    'Pricing': ['price', 'pricing', 'cost', 'fee', 'payment', 'transparent', 'expensive'],
    'Model Selection': ['model', 'talent', 'portfolio', 'photo', 'profile', 'quality'],
    'User Experience': ['easy', 'convenient', 'simple', 'interface', 'navigation', 'back button'],
    'Speed': ['fast', 'quick', 'slow', 'time', 'delay', 'loading'],
    'Features': ['feature', 'function', 'tool', 'option', 'capability'],
    'Booking Process': ['booking', 'request', 'confirm', 'contract', 'process']
}

# Count mentions per priority area
priority_counts = {}
for priority, keywords in priority_keywords.items():
    count = 0
    for text in df['text_clean']:
        if any(keyword in text for keyword in keywords):
            count += 1
    priority_counts[priority] = count

# Sort by frequency
priority_sorted = sorted(priority_counts.items(), key=lambda x: x[1], reverse=True)

print("Priority areas by mention frequency:")
for priority, count in priority_sorted:
    pct = (count / len(df)) * 100
    print(f"  {priority}: {count} mentions ({pct:.1f}%)")
print()

# ============================================================================
# SPECIFIC PAIN POINTS & REQUESTS
# ============================================================================

print("="*80)
print("IDENTIFYING PAIN POINTS & REQUESTS")
print("="*80 + "\n")

# Look for common patterns
pain_point_patterns = [
    (r'need|want|wish|would like|looking for', 'Feature Requests'),
    (r'difficult|hard|confusing|complicated|issue|problem', 'Pain Points'),
    (r'missing|lack|no|not|don\'t have|doesn\'t', 'Missing Features'),
    (r'slow|lag|delay|wait', 'Performance Issues'),
    (r'great|good|helpful|useful|convenient|easy', 'Positive Feedback')
]

pattern_counts = {name: 0 for _, name in pain_point_patterns}
pattern_examples = {name: [] for _, name in pain_point_patterns}

for text in df['text']:
    for pattern, name in pain_point_patterns:
        if re.search(pattern, str(text), re.IGNORECASE):
            pattern_counts[name] += 1
            if len(pattern_examples[name]) < 3:  # Store max 3 examples
                # Extract sentence containing the pattern
                sentences = str(text).split('.')
                for sent in sentences:
                    if re.search(pattern, sent, re.IGNORECASE):
                        pattern_examples[name].append(sent.strip()[:150] + "...")
                        break

print("Feedback patterns:")
for name, count in pattern_counts.items():
    pct = (count / len(df)) * 100
    print(f"\n{name}: {count} mentions ({pct:.1f}%)")
    if pattern_examples[name]:
        print("  Examples:")
        for ex in pattern_examples[name][:2]:
            print(f"    - {ex}")

# ============================================================================
# VISUALIZATIONS
# ============================================================================

print("\n" + "="*80)
print("GENERATING VISUALIZATIONS")
print("="*80 + "\n")

# 1. Category Distribution
print("1. Creating category distribution chart...")
fig = go.Figure(data=[
    go.Bar(
        x=list(category_dist.values),
        y=list(category_dist.index),
        orientation='h',
        marker_color='steelblue'
    )
])
fig.update_layout(
    title='VOC Categories Distribution',
    xaxis_title='Count',
    yaxis_title='Category',
    height=400
)
fig.write_html(f'{OUTPUT_DIR}/categories_distribution.html')
print(f"✓ Saved: {OUTPUT_DIR}/categories_distribution.html")

# 2. User Type Distribution
print("2. Creating user type distribution chart...")
fig = go.Figure(data=[
    go.Pie(
        labels=user_type_dist.index,
        values=user_type_dist.values,
        hole=0.3
    )
])
fig.update_layout(title='User Type Distribution', height=500)
fig.write_html(f'{OUTPUT_DIR}/user_type_distribution.html')
print(f"✓ Saved: {OUTPUT_DIR}/user_type_distribution.html")

# 3. Priority Areas
print("3. Creating priority areas chart...")
priorities, counts = zip(*priority_sorted)
fig = go.Figure(data=[
    go.Bar(
        x=list(counts),
        y=list(priorities),
        orientation='h',
        marker_color='teal'
    )
])
fig.update_layout(
    title='Priority Areas by Mention Frequency',
    xaxis_title='Mentions',
    yaxis_title='Priority Area',
    height=500,
    yaxis={'categoryorder': 'total ascending'}
)
fig.write_html(f'{OUTPUT_DIR}/priority_areas.html')
print(f"✓ Saved: {OUTPUT_DIR}/priority_areas.html")

# 4. Theme Distribution
print("4. Creating theme distribution chart...")
fig = go.Figure(data=[
    go.Bar(
        x=list(theme_dist.index),
        y=list(theme_dist.values),
        marker_color='purple'
    )
])
fig.update_layout(
    title='Theme Distribution from Topic Modeling',
    xaxis_title='Theme',
    yaxis_title='Count',
    height=400
)
fig.write_html(f'{OUTPUT_DIR}/theme_distribution.html')
print(f"✓ Saved: {OUTPUT_DIR}/theme_distribution.html")

# 5. Feedback Patterns
print("5. Creating feedback patterns chart...")
fig = go.Figure(data=[
    go.Bar(
        x=list(pattern_counts.values()),
        y=list(pattern_counts.keys()),
        orientation='h',
        marker_color='coral'
    )
])
fig.update_layout(
    title='Feedback Patterns',
    xaxis_title='Mentions',
    yaxis_title='Pattern Type',
    height=400
)
fig.write_html(f'{OUTPUT_DIR}/feedback_patterns.html')
print(f"✓ Saved: {OUTPUT_DIR}/feedback_patterns.html")

# 6. Word Cloud
print("6. Creating word cloud...")
wordcloud = WordCloud(
    width=1600,
    height=800,
    background_color='white',
    max_words=100
).generate(all_text)

plt.figure(figsize=(16, 8))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off')
plt.title('Most Common Words in VOC Feedback', fontsize=20)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/voc_wordcloud.png', dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Saved: {OUTPUT_DIR}/voc_wordcloud.png")

# ============================================================================
# EXPORT DATA
# ============================================================================

print("\n" + "="*80)
print("EXPORTING DATA")
print("="*80 + "\n")

# 1. Theme assignments
theme_export = df[['ID', 'Name', 'User Type', 'Categories', 'primary_theme', 'theme_confidence', 'text']].copy()
theme_export.columns = ['ID', 'Name', 'User Type', 'Categories', 'Assigned Theme', 'Confidence', 'Text']
theme_export.to_csv(f'{OUTPUT_DIR}/voc_with_themes.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/voc_with_themes.csv")

# 2. Theme keywords
theme_keywords = []
for i, words in enumerate(lda_topics_words, 1):
    theme_keywords.append({
        'Theme': i,
        'Top_Keywords': ', '.join(words[:10]),
        'Count': theme_dist.get(i, 0)
    })
pd.DataFrame(theme_keywords).to_csv(f'{OUTPUT_DIR}/theme_keywords.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/theme_keywords.csv")

# 3. Priority areas
priority_df = pd.DataFrame([
    {'Priority Area': k, 'Mentions': v, 'Percentage': f"{(v/len(df))*100:.1f}%"}
    for k, v in priority_sorted
])
priority_df.to_csv(f'{OUTPUT_DIR}/priority_areas.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/priority_areas.csv")

# 4. Keyword frequency
keyword_df = pd.DataFrame(all_keywords, columns=['Keyword', 'Frequency'])
keyword_df.to_csv(f'{OUTPUT_DIR}/voc_keywords.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/voc_keywords.csv")

# 5. Category statistics
category_stats = pd.DataFrame({
    'Category': category_dist.index,
    'Count': category_dist.values,
    'Percentage': [(c/len(df))*100 for c in category_dist.values]
})
category_stats.to_csv(f'{OUTPUT_DIR}/category_statistics.csv', index=False, encoding='utf-8-sig')
print(f"✓ Saved: {OUTPUT_DIR}/category_statistics.csv")

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
    <title>VOC Thematic Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
            color: #f5576c;
            border-bottom: 2px solid #f5576c;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
            background-color: #f5576c;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .theme-box {{
            background: #fff3e0;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #ff9800;
        }}
        .theme-title {{
            font-weight: 600;
            color: #e65100;
            margin-bottom: 5px;
        }}
        .theme-keywords {{
            color: #666;
            font-size: 14px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .chart-link {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
            text-decoration: none;
            color: #f5576c;
            border: 2px solid #f5576c;
            transition: all 0.3s;
        }}
        .chart-link:hover {{
            background: #f5576c;
            color: white;
        }}
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .image-container img {{
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .example-box {{
            background: #f1f8f4;
            padding: 12px;
            border-radius: 6px;
            margin: 8px 0;
            font-size: 14px;
            border-left: 3px solid #4caf50;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💬 VOC Thematic Analysis Report</h1>
        <div class="subtitle">Customer feedback themes and priorities analysis</div>
    </div>

    <div class="section">
        <h2>📈 Overview Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number">{len(df)}</div>
                <div class="stat-label">Total VOC Entries</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{n_topics}</div>
                <div class="stat-label">Identified Themes</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(priority_keywords)}</div>
                <div class="stat-label">Priority Areas</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(all_keywords)}</div>
                <div class="stat-label">Unique Keywords</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🎯 Top Priority Areas</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Priority Area</th>
                    <th>Mentions</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{i+1}</td><td>{priority}</td><td>{count}</td><td>{(count/len(df))*100:.1f}%</td></tr>" 
                          for i, (priority, count) in enumerate(priority_sorted)])}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🔍 Identified Themes (Topic Modeling)</h2>
        {''.join([f'''
        <div class="theme-box">
            <div class="theme-title">Theme {i}: {words[0].title()} & {words[1].title()}</div>
            <div class="theme-keywords">Keywords: {', '.join(words[:8])}</div>
            <div style="margin-top: 8px; color: #999; font-size: 13px;">
                {theme_dist.get(i, 0)} entries ({(theme_dist.get(i, 0)/len(df))*100:.1f}%)
            </div>
        </div>
        ''' for i, words in enumerate(lda_topics_words, 1)])}
    </div>

    <div class="section">
        <h2>📊 Feedback Patterns</h2>
        <table>
            <thead>
                <tr>
                    <th>Pattern Type</th>
                    <th>Mentions</th>
                    <th>Examples</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f'''<tr>
                    <td><strong>{name}</strong></td>
                    <td>{count} ({(count/len(df))*100:.1f}%)</td>
                    <td>{"<br>".join([f'<div class="example-box">{ex}</div>' for ex in pattern_examples[name][:2]])}</td>
                </tr>''' for name, count in pattern_counts.items()])}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>🔑 Top 30 Keywords</h2>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Keyword</th>
                    <th>Frequency</th>
                </tr>
            </thead>
            <tbody>
                {''.join([f"<tr><td>{i+1}</td><td>{kw}</td><td>{count}</td></tr>" 
                          for i, (kw, count) in enumerate(all_keywords[:30])])}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>☁️ Word Cloud</h2>
        <div class="image-container">
            <img src="voc_wordcloud.png" alt="VOC Word Cloud">
        </div>
    </div>

    <div class="section">
        <h2>📊 Interactive Charts</h2>
        <div class="chart-grid">
            <a href="categories_distribution.html" class="chart-link" target="_blank">
                📁 Categories Distribution
            </a>
            <a href="user_type_distribution.html" class="chart-link" target="_blank">
                👥 User Type Distribution
            </a>
            <a href="priority_areas.html" class="chart-link" target="_blank">
                🎯 Priority Areas
            </a>
            <a href="theme_distribution.html" class="chart-link" target="_blank">
                🔍 Theme Distribution
            </a>
            <a href="feedback_patterns.html" class="chart-link" target="_blank">
                💬 Feedback Patterns
            </a>
        </div>
    </div>

    <div class="section">
        <h2>📁 Exported Files</h2>
        <ul>
            <li><strong>voc_with_themes.csv</strong> - All VOC entries with assigned themes</li>
            <li><strong>theme_keywords.csv</strong> - Keywords for each theme</li>
            <li><strong>priority_areas.csv</strong> - Priority areas with frequencies</li>
            <li><strong>voc_keywords.csv</strong> - All keywords with frequencies</li>
            <li><strong>category_statistics.csv</strong> - Category breakdown</li>
        </ul>
    </div>

    <div class="section">
        <h2>💡 Key Insights</h2>
        <ul>
            <li><strong>Most mentioned priority:</strong> {priority_sorted[0][0]} ({priority_sorted[0][1]} mentions)</li>
            <li><strong>Most common category:</strong> {category_dist.index[0]} ({category_dist.values[0]} entries)</li>
            <li><strong>Primary user type:</strong> {user_type_dist.index[0]} ({user_type_dist.values[0]} entries)</li>
            <li><strong>Feature requests:</strong> {pattern_counts.get('Feature Requests', 0)} mentions</li>
            <li><strong>Pain points:</strong> {pattern_counts.get('Pain Points', 0)} mentions</li>
            <li><strong>Positive feedback:</strong> {pattern_counts.get('Positive Feedback', 0)} mentions</li>
        </ul>
    </div>
</body>
</html>
"""

with open(f'{OUTPUT_DIR}/voc_analysis_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Saved: {OUTPUT_DIR}/voc_analysis_report.html")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ SCRIPT 4 COMPLETE!")
print("="*80 + "\n")

print("📊 Summary:")
print(f"  • Analyzed {len(df)} VOC entries")
print(f"  • Identified {n_topics} main themes via topic modeling")
print(f"  • Extracted {len(priority_keywords)} priority areas")
print(f"  • Found {len(all_keywords)} unique keywords")
print(f"  • Top priority: {priority_sorted[0][0]} ({priority_sorted[0][1]} mentions)")
print(f"\n📁 All outputs saved to: {OUTPUT_DIR}/")
print(f"\n🌐 Open 'voc_analysis_report.html' in your browser to view the interactive report!")
print("\n" + "="*80 + "\n")
