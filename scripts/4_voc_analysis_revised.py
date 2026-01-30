#!/usr/bin/env python3
"""
VOC Thematic Analysis - REVISED
Extracts meaningful phrases and themes from customer feedback
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from collections import Counter
import json

# NLP libraries
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from deep_translator import GoogleTranslator

print("=" * 80)
print("VOC THEMATIC ANALYSIS - REVISED")
print("=" * 80)

# Setup paths
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "voc_analysis_revised"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"\n📁 Output directory: {OUTPUT_DIR}")

# Load data
print("\n📊 Loading VOC data...")
voc_df = pd.read_csv(DATA_DIR / "VOC_Search.csv")
print(f"   Loaded {len(voc_df)} VOC entries")

# -------------------------------------------------------------------
# TRANSLATION
# -------------------------------------------------------------------
print("\n🌐 Translating Korean feedback to English...")

translator = GoogleTranslator(source='ko', target='en')

def safe_translate(text):
    """Translate with error handling"""
    if pd.isna(text) or text.strip() == '':
        return ''
    try:
        # Split into chunks (Google Translate has char limits)
        chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
        translated_chunks = [translator.translate(chunk) for chunk in chunks]
        return ' '.join(translated_chunks)
    except Exception as e:
        print(f"   Translation error: {e}")
        return text

# Translate if not already done
if 'ENG' not in voc_df.columns:
    voc_df['ENG'] = voc_df['KOR'].apply(safe_translate)
    print("   ✅ Translation complete")
else:
    print("   ✅ Using existing translations")

# -------------------------------------------------------------------
# PHRASE EXTRACTION
# -------------------------------------------------------------------
print("\n🔍 Extracting meaningful phrases...")

def extract_korean_phrases(text):
    """Extract 2-4 word Korean phrases"""
    if pd.isna(text) or text.strip() == '':
        return []
    
    # Simple tokenization (split by spaces and punctuation)
    tokens = re.findall(r'[\w가-힣]+', text)
    
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

def extract_english_phrases(text):
    """Extract 2-4 word English phrases"""
    if pd.isna(text) or text.strip() == '':
        return []
    
    # Tokenize
    tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    # Common English stop words to filter
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                  'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 
                  'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 
                  'does', 'did', 'will', 'would', 'should', 'could', 'may', 
                  'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 
                  'he', 'she', 'it', 'we', 'they', 'them', 'their', 'my', 'your',
                  'very', 'too', 'also', 'just', 'so', 'than', 'such'}
    
    phrases = []
    # 2-word phrases
    for i in range(len(tokens) - 1):
        if tokens[i] not in stop_words or tokens[i+1] not in stop_words:
            phrase = f"{tokens[i]} {tokens[i+1]}"
            phrases.append(phrase)
    
    # 3-word phrases  
    for i in range(len(tokens) - 2):
        phrase = f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}"
        # At least one word should not be a stop word
        if any(t not in stop_words for t in [tokens[i], tokens[i+1], tokens[i+2]]):
            phrases.append(phrase)
    
    return phrases

# Extract phrases
print("   Extracting Korean phrases...")
voc_df['korean_phrases'] = voc_df['KOR'].apply(extract_korean_phrases)

print("   Extracting English phrases...")
voc_df['english_phrases'] = voc_df['ENG'].apply(extract_english_phrases)

# Get all phrases
all_korean_phrases = []
all_english_phrases = []

for phrases in voc_df['korean_phrases']:
    all_korean_phrases.extend(phrases)

for phrases in voc_df['english_phrases']:
    all_english_phrases.extend(phrases)

# Count phrase frequencies
korean_phrase_counts = Counter(all_korean_phrases)
english_phrase_counts = Counter(all_english_phrases)

print(f"   ✅ Extracted {len(korean_phrase_counts)} unique Korean phrases")
print(f"   ✅ Extracted {len(english_phrase_counts)} unique English phrases")

# -------------------------------------------------------------------
# THEME IDENTIFICATION
# -------------------------------------------------------------------
print("\n🎯 Identifying themes from phrases...")

# Define theme keywords (expanded with phrases)
theme_definitions = {
    'Search & Filter': [
        'search', 'filter', 'finding', 'discovery', 'browse', 'looking for',
        'search function', 'filter option', 'find model', 'model search',
        '검색', '필터', '찾기', '탐색', '발견',
        '검색 기능', '필터 옵션', '모델 찾기', '인종 필터', '국적 필터'
    ],
    'Pricing & Transparency': [
        'price', 'pricing', 'cost', 'fee', 'transparent', 'clarity', 'clear pricing',
        'pricing transparency', 'price information', 'cost breakdown',
        '가격', '금액', '비용', '투명', '명확',
        '가격 투명성', '금액 정보', '비용 명확', '가격이 명확'
    ],
    'Communication': [
        'chat', 'message', 'communication', 'response', 'reply', 'conversation',
        'messaging', 'auto translation', 'language barrier',
        '채팅', '메시지', '소통', '의사소통', '응답', '대화',
        '자동 번역', '번역 기능', '언어 장벽', '소통 편함'
    ],
    'User Experience': [
        'easy', 'convenient', 'simple', 'user friendly', 'smooth', 'comfortable',
        'ease of use', 'convenient process', 'simple interface',
        '편함', '편리', '쉬움', '간편', '사용하기 쉬움',
        '편리한 과정', '간편한 인터페이스', '쓰기 편함'
    ],
    'vs Agency/Traditional': [
        'agency', 'traditional', 'compared to', 'better than', 'easier than',
        'vs agency', 'agency comparison', 'traditional method',
        '에이전시', '기존', '비교', '대행사',
        '에이전시 대비', '기존 방식', '에이전시보다 편함'
    ],
    'Feature Requests': [
        'would be good', 'wish', 'hope', 'suggest', 'recommendation', 'need',
        'feature request', 'want to see', 'missing feature',
        '있으면 좋겠', '필요', '바람', '추천', '제안',
        '기능 추가', '필요한 기능', '없어서 아쉬움'
    ],
    'Model Selection': [
        'model', 'talent', 'portfolio', 'profile', 'selection', 'choosing',
        'model selection', 'talent pool', 'model profile',
        '모델', '프로필', '포트폴리오', '선택',
        '모델 선택', '모델 프로필', '모델 포트폴리오'
    ],
    'Booking Process': [
        'booking', 'request', 'confirmation', 'scheduling', 'process',
        'booking process', 'request flow', 'confirmation process',
        '예약', '요청', '확인', '스케줄', '진행',
        '예약 과정', '요청 프로세스', '섭외 과정'
    ],
}

def assign_themes(text_korean, text_english):
    """Assign themes based on keyword matching in both languages"""
    themes = []
    text_combined = f"{text_korean} {text_english}".lower()
    
    for theme, keywords in theme_definitions.items():
        for keyword in keywords:
            if keyword.lower() in text_combined:
                themes.append(theme)
                break  # One match per theme is enough
    
    return themes if themes else ['Other']

voc_df['themes'] = voc_df.apply(
    lambda row: assign_themes(str(row['KOR']), str(row['ENG'])), 
    axis=1
)

# Count theme occurrences
theme_counts = Counter()
for themes in voc_df['themes']:
    theme_counts.update(themes)

print("   ✅ Theme distribution:")
for theme, count in theme_counts.most_common():
    print(f"      {theme}: {count}")

# -------------------------------------------------------------------
# SAVE DATA
# -------------------------------------------------------------------
print("\n💾 Saving analysis data...")

# Save main data with themes
voc_df_export = voc_df[[
    'Categories', 'User Type', 'KOR', 'ENG', 'themes',
    'korean_phrases', 'english_phrases'
]].copy()

# Convert lists to strings for CSV
voc_df_export['themes_str'] = voc_df_export['themes'].apply(lambda x: '; '.join(x))
voc_df_export['korean_phrases_str'] = voc_df_export['korean_phrases'].apply(lambda x: '; '.join(x[:10]))  # Top 10
voc_df_export['english_phrases_str'] = voc_df_export['english_phrases'].apply(lambda x: '; '.join(x[:10]))

voc_df_export.to_csv(OUTPUT_DIR / "voc_with_themes_and_phrases.csv", index=False, encoding='utf-8-sig')

# Save phrase frequencies
pd.DataFrame(
    korean_phrase_counts.most_common(100),
    columns=['Phrase', 'Frequency']
).to_csv(OUTPUT_DIR / "korean_phrases_top100.csv", index=False, encoding='utf-8-sig')

pd.DataFrame(
    english_phrase_counts.most_common(100),
    columns=['Phrase', 'Frequency']
).to_csv(OUTPUT_DIR / "english_phrases_top100.csv", index=False, encoding='utf-8-sig')

# -------------------------------------------------------------------
# CREATE INTERACTIVE HTML REPORT
# -------------------------------------------------------------------
print("\n📄 Creating interactive HTML report...")

# Prepare data for clickable themes
voc_by_theme = {}
for theme in theme_definitions.keys():
    voc_by_theme[theme] = voc_df[voc_df['themes'].apply(lambda x: theme in x)][[
        'Categories', 'User Type', 'KOR', 'ENG'
    ]].to_dict('records')

# Convert to JSON for embedding in HTML
voc_data_json = json.dumps(voc_by_theme, ensure_ascii=False)

html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VOC Thematic Analysis - Revised</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            padding: 40px 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        h1 {{
            font-size: 2.5em;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin-bottom: 40px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }}
        
        .theme-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .theme-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }}
        
        .theme-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }}
        
        .theme-card h3 {{
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        
        .theme-count {{
            font-size: 2em;
            font-weight: bold;
            opacity: 0.9;
        }}
        
        .theme-label {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            overflow-y: auto;
        }}
        
        .modal-content {{
            background: white;
            max-width: 1200px;
            margin: 50px auto;
            padding: 40px;
            border-radius: 12px;
            position: relative;
        }}
        
        .close-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 2em;
            cursor: pointer;
            color: #7f8c8d;
            transition: color 0.3s;
        }}
        
        .close-btn:hover {{
            color: #e74c3c;
        }}
        
        .feedback-item {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #3498db;
        }}
        
        .feedback-meta {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-client {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        
        .badge-model {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        
        .feedback-text {{
            margin-bottom: 15px;
        }}
        
        .korean-text {{
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
        }}
        
        .english-text {{
            background: #f1f8ff;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #c8e1ff;
            color: #0366d6;
        }}
        
        .text-label {{
            font-size: 0.8em;
            font-weight: 600;
            color: #7f8c8d;
            margin-bottom: 5px;
        }}
        
        .phrase-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 15px;
        }}
        
        .phrase-tag {{
            background: #667eea;
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 VOC Thematic Analysis</h1>
        <p class="subtitle">Customer Feedback Analysis with Phrase Extraction & Theme Identification</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(voc_df)}</div>
                <div class="stat-label">Total Feedback Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(theme_counts)}</div>
                <div class="stat-label">Identified Themes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(korean_phrase_counts)}</div>
                <div class="stat-label">Korean Phrases</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(english_phrase_counts)}</div>
                <div class="stat-label">English Phrases</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 Themes (Click to View Feedback)</h2>
            <div class="theme-grid">
"""

# Add theme cards
colors = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
    'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
    'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
]

for idx, (theme, count) in enumerate(theme_counts.most_common()):
    color = colors[idx % len(colors)]
    html_template += f"""
                <div class="theme-card" style="background: {color};" data-theme="{theme}">
                    <h3>{theme}</h3>
                    <div class="theme-count">{count}</div>
                    <div class="theme-label">feedback entries</div>
                </div>
"""

html_template += f"""
            </div>
        </div>
    </div>
    
    <!-- Modal for showing feedback -->
    <div id="feedbackModal" class="modal">
        <div class="modal-content">
            <span class="close-btn" onclick="closeModal()">&times;</span>
            <h2 id="modalTitle"></h2>
            <div id="modalBody"></div>
        </div>
    </div>
    
    <script>
        const vocData = {voc_data_json};
        
        function escapeHtml(text) {{
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function showThemeFeedback(theme) {{
            const modal = document.getElementById('feedbackModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');
            
            title.textContent = theme + ' - Customer Feedback';
            
            const feedbackList = vocData[theme] || [];
            
            if (feedbackList.length === 0) {{
                body.innerHTML = '<p>No feedback found for this theme.</p>';
            }} else {{
                let html = `<p style="color: #7f8c8d; margin-bottom: 20px;">Found ${{feedbackList.length}} feedback entries for this theme.</p>`;
                
                feedbackList.forEach((item, idx) => {{
                    const userBadge = item['User Type'] === 'Client' ? 
                        '<span class="badge badge-client">Client</span>' : 
                        '<span class="badge badge-model">Model</span>';
                    
                    html += `
                        <div class="feedback-item">
                            <div class="feedback-meta">
                                <span style="font-weight: 600; color: #2c3e50;">#${{idx + 1}}</span>
                                ${{userBadge}}
                                <span>${{item.Categories}}</span>
                            </div>
                            <div class="feedback-text">
                                <div class="text-label">🇰🇷 Korean Original:</div>
                                <div class="korean-text">${{escapeHtml(item.KOR)}}</div>
                                
                                <div class="text-label">🇬🇧 English Translation:</div>
                                <div class="english-text">${{escapeHtml(item.ENG)}}</div>
                            </div>
                        </div>
                    `;
                }});
                body.innerHTML = html;
            }}
            
            modal.style.display = 'block';
        }}
        
        function closeModal() {{
            document.getElementById('feedbackModal').style.display = 'none';
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('feedbackModal');
            if (event.target === modal) {{
                modal.style.display = 'none';
            }}
        }}
        
        // Add click event listeners to all theme cards
        document.addEventListener('DOMContentLoaded', function() {{
            const themeCards = document.querySelectorAll('.theme-card');
            themeCards.forEach(card => {{
                card.addEventListener('click', function() {{
                    const theme = this.getAttribute('data-theme');
                    showThemeFeedback(theme);
                }});
            }});
            
            console.log('VOC Interactive Dashboard loaded. Click on any theme card to view feedback.');
        }});
        
        // Support Escape key to close modal
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
"""

# Save HTML
with open(OUTPUT_DIR / "voc_analysis_interactive.html", 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"   ✅ Interactive report saved: voc_analysis_interactive.html")

print("\n" + "=" * 80)
print("✅ VOC ANALYSIS COMPLETE!")
print("=" * 80)
print(f"\n📂 All outputs saved to: {OUTPUT_DIR}")
print("\n📊 Generated files:")
print("   • voc_analysis_interactive.html - Interactive clickable report")
print("   • voc_with_themes_and_phrases.csv - Full data with themes & phrases")
print("   • korean_phrases_top100.csv - Top 100 Korean phrases")
print("   • english_phrases_top100.csv - Top 100 English phrases")
print("\n🎯 Open voc_analysis_interactive.html in your browser!")
