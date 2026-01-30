#!/usr/bin/env python3
"""
VOC Thematic Analysis - Sentence-Level Extraction
Extracts specific sentences that match each theme
"""

import pandas as pd
import numpy as np
from pathlib import Path
import re
from collections import Counter, defaultdict
import json

# NLP libraries
from deep_translator import GoogleTranslator

print("=" * 80)
print("VOC THEMATIC ANALYSIS - SENTENCE-LEVEL")
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
    print("   Translating all feedback...")
    voc_df['ENG'] = voc_df['KOR'].apply(safe_translate)
    print("   ✅ Translation complete")
else:
    print("   ✅ English translations already exist")

# -------------------------------------------------------------------
# SENTENCE SPLITTING
# -------------------------------------------------------------------
print("\n✂️  Splitting feedback into sentences...")

def split_into_sentences(text):
    """Split Korean text into sentences"""
    if pd.isna(text) or text.strip() == '':
        return []
    
    # Split on common Korean sentence enders
    # • for bullet points, . for periods, ? for questions, ! for exclamations
    sentences = re.split(r'[•\.?!。]\s*', str(text))
    
    # Clean and filter
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    return sentences

voc_df['sentences_kor'] = voc_df['KOR'].apply(split_into_sentences)

print(f"   ✅ Extracted sentences from {len(voc_df)} feedback entries")

# -------------------------------------------------------------------
# THEME DEFINITIONS
# -------------------------------------------------------------------

theme_definitions = {
    'Search & Filter': [
        'search', 'filter', 'finding', 'discovery', 'browse', 'looking for',
        'search function', 'filter option', 'find model', 'model search',
        '검색', '필터', '찾기', '탐색', '발견', '서칭',
        '검색 기능', '필터 옵션', '모델 찾기', '인종 필터', '국적 필터'
    ],
    'Pricing & Transparency': [
        'price', 'pricing', 'cost', 'fee', 'transparent', 'clarity', 'clear pricing',
        'pricing transparency', 'price information', 'cost breakdown',
        '가격', '금액', '비용', '투명', '명확',
        '가격 투명성', '금액 정보', '비용 명확', '가격이 명확', '불투명'
    ],
    'Communication': [
        'chat', 'message', 'communication', 'response', 'reply', 'conversation',
        'messaging', 'auto translation', 'language barrier',
        '채팅', '메시지', '소통', '의사소통', '응답', '대화',
        '자동 번역', '번역 기능', '언어 장벽', '소통 편함', '편했다'
    ],
    'User Experience': [
        'easy', 'convenient', 'simple', 'user friendly', 'smooth', 'comfortable',
        'ease of use', 'convenient process', 'simple interface', 'satisfied',
        '편함', '편리', '쉬움', '간편', '사용하기 쉬움', '만족',
        '편리한 과정', '간편한 인터페이스', '쓰기 편함'
    ],
    'vs Agency/Traditional': [
        'agency', 'traditional', 'compared to', 'better than', 'easier than',
        'vs agency', 'agency comparison', 'traditional method',
        '에이전시', '기존', '비교', '대행사', '대비',
        '에이전시 대비', '기존 방식', '에이전시보다 편함'
    ],
    'Feature Requests': [
        'would be good', 'wish', 'hope', 'suggest', 'recommendation', 'need',
        'feature request', 'want to see', 'missing feature',
        '있으면 좋겠', '필요', '바람', '추천', '제안', '아쉬',
        '기능 추가', '필요한 기능', '없어서 아쉬움', '좋을 것 같다'
    ],
    'Model Selection': [
        'model', 'talent', 'portfolio', 'profile', 'selection', 'choosing',
        'model selection', 'talent pool', 'model profile',
        '모델', '프로필', '포트폴리오', '선택',
        '모델 선택', '모델 프로필', '모델 포트폴리오', '흑인 모델', '국내거주 모델'
    ],
    'Booking Process': [
        'booking', 'request', 'confirmation', 'scheduling', 'process',
        'booking process', 'request flow', 'confirmation process',
        '예약', '요청', '확인', '스케줄', '진행',
        '예약 과정', '요청 프로세스', '섭외 과정'
    ],
}

# -------------------------------------------------------------------
# SENTENCE-LEVEL THEME MATCHING
# -------------------------------------------------------------------
print("\n🎯 Matching sentences to themes...")

def match_sentence_to_themes(sentence):
    """Find which themes this sentence matches"""
    themes = []
    sentence_lower = sentence.lower()
    
    for theme, keywords in theme_definitions.items():
        for keyword in keywords:
            if keyword.lower() in sentence_lower:
                themes.append(theme)
                break  # One match per theme per sentence
    
    return themes

# Build theme-to-sentences mapping
theme_sentences = defaultdict(list)
theme_voc_ids = defaultdict(set)  # Track unique VOC IDs per theme

for idx, row in voc_df.iterrows():
    voc_id = row['ID'] if pd.notna(row['ID']) else idx
    user_type = row['User Type']
    category = row['Categories']
    
    for sentence_kor in row['sentences_kor']:
        # Check which themes this sentence matches
        themes = match_sentence_to_themes(sentence_kor)
        
        if themes:
            # Translate just this sentence
            print(f"   Translating sentence {len(theme_sentences)} ...", end='\r')
            sentence_eng = safe_translate(sentence_kor)
            
            # Add to each matching theme
            for theme in themes:
                theme_sentences[theme].append({
                    'voc_id': voc_id,
                    'user_type': user_type,
                    'category': category,
                    'sentence_kor': sentence_kor,
                    'sentence_eng': sentence_eng
                })
                theme_voc_ids[theme].add(voc_id)  # Track unique VOC ID

print(f"\n   ✅ Matched {sum(len(v) for v in theme_sentences.values())} sentences across {len(theme_sentences)} themes")

# Print theme distribution
print("\n   Theme distribution:")
for theme in sorted(theme_definitions.keys()):
    count = len(theme_sentences.get(theme, []))
    print(f"      {theme}: {count} sentences")

# -------------------------------------------------------------------
# CREATE INTERACTIVE HTML REPORT
# -------------------------------------------------------------------
print("\n📄 Creating interactive HTML report...")

# Convert to JSON for embedding in HTML
voc_data_json = json.dumps(theme_sentences, ensure_ascii=False, default=str)

# Create VOC counts for each theme
voc_counts_json = json.dumps({theme: len(ids) for theme, ids in theme_voc_ids.items()}, ensure_ascii=False)

html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VOC Thematic Analysis - Interactive</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background-color: #f5f7fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        h1 {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            opacity: 0.9;
            font-size: 18px;
        }}
        
        .themes-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .theme-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.3s;
            border-left: 5px solid #667eea;
        }}
        
        .theme-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .theme-icon {{
            font-size: 48px;
            margin-bottom: 15px;
        }}
        
        .theme-title {{
            font-size: 20px;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .theme-count {{
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}
        
        .theme-label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            overflow-y: auto;
        }}
        
        .modal-content {{
            background-color: white;
            margin: 50px auto;
            padding: 40px;
            border-radius: 15px;
            width: 90%;
            max-width: 1000px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            position: relative;
        }}
        
        .close-btn {{
            position: absolute;
            top: 20px;
            right: 30px;
            font-size: 36px;
            font-weight: 300;
            color: #999;
            cursor: pointer;
            transition: color 0.3s;
        }}
        
        .close-btn:hover {{
            color: #333;
        }}
        
        #modalTitle {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .feedback-item {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
        }}
        
        .feedback-meta {{
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 15px;
            font-size: 14px;
            color: #7f8c8d;
        }}
        
        .badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-client {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        
        .badge-model {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .feedback-text {{
            margin-top: 15px;
        }}
        
        .text-label {{
            font-size: 13px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .korean-text {{
            font-size: 15px;
            line-height: 1.8;
            color: #2c3e50;
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 6px;
        }}
        
        .english-text {{
            font-size: 14px;
            line-height: 1.7;
            color: #555;
            padding: 15px;
            background: white;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💬 VOC Thematic Analysis</h1>
            <p class="subtitle">Click on any theme to view relevant feedback sentences</p>
        </div>
        
        <div class="themes-grid">
"""

# Add theme cards
theme_icons = {
    'Search & Filter': '🔍',
    'Pricing & Transparency': '💰',
    'Communication': '💬',
    'User Experience': '⭐',
    'vs Agency/Traditional': '🏢',
    'Feature Requests': '💡',
    'Model Selection': '👤',
    'Booking Process': '📅'
}

for theme in sorted(theme_definitions.keys()):
    count = len(theme_sentences.get(theme, []))
    icon = theme_icons.get(theme, '📋')
    
    html_template += f"""
            <div class="theme-card" data-theme="{theme}" onclick="showThemeFeedback('{theme}')">
                <div class="theme-icon">{icon}</div>
                <div class="theme-title">{theme}</div>
                <div class="theme-count">{count}</div>
                <div class="theme-label">sentence{' matches' if count != 1 else ' match'}</div>
            </div>
"""

html_template += f"""
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
        const vocCounts = {voc_counts_json};
        
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
            
            title.textContent = theme;
            
            const sentences = vocData[theme] || [];
            
            if (sentences.length === 0) {{
                body.innerHTML = '<p style="color: #999;">No sentences found for this theme.</p>';
            }} else {{
                // Group sentences by VOC ID
                const groupedByVoc = {{}};
                sentences.forEach(item => {{
                    const vocId = item.voc_id;
                    if (!groupedByVoc[vocId]) {{
                        groupedByVoc[vocId] = [];
                    }}
                    groupedByVoc[vocId].push(item);
                }});
                
                const uniqueVocCount = Object.keys(groupedByVoc).length;
                const totalSentences = sentences.length;
                
                let html = `<p style="color: #7f8c8d; margin-bottom: 20px; font-size: 14px; line-height: 1.6;">
                    Found <strong>${{totalSentences}} relevant sentence${{totalSentences > 1 ? 's' : ''}}</strong> 
                    from <strong>${{uniqueVocCount}} customer VOC${{uniqueVocCount > 1 ? 's' : ''}}</strong> 
                    related to ${{theme.toLowerCase()}}.
                </p>`;
                
                // Render grouped by VOC ID
                Object.keys(groupedByVoc).sort().forEach(vocId => {{
                    const vocSentences = groupedByVoc[vocId];
                    const firstItem = vocSentences[0];
                    
                    const userBadge = firstItem.user_type === 'Client' ? 
                        '<span class="badge badge-client">Client</span>' : 
                        '<span class="badge badge-model">Model</span>';
                    
                    html += `
                        <div class="feedback-item">
                            <div class="feedback-meta">
                                <span style="font-weight: 700; color: #667eea; font-size: 15px;">VOC #${{vocId}}</span>
                                ${{userBadge}}
                                <span>${{firstItem.category}}</span>
                            </div>
                    `;
                    
                    // Show all sentences from this VOC
                    vocSentences.forEach((item, idx) => {{
                        html += `
                            <div class="feedback-text" style="margin-top: 15px; ${{idx > 0 ? 'border-top: 1px dashed #e0e0e0; padding-top: 15px;' : ''}}">
                                <div class="text-label">🇰🇷 Korean</div>
                                <div class="korean-text">${{escapeHtml(item.sentence_kor)}}</div>
                                
                                <div class="text-label">🇬🇧 English</div>
                                <div class="english-text">${{escapeHtml(item.sentence_eng)}}</div>
                            </div>
                        `;
                    }});
                    
                    html += `</div>`;
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
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
"""

# Save HTML report
output_file = OUTPUT_DIR / "voc_analysis_interactive.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"✅ Saved interactive report: {output_file}")

# -------------------------------------------------------------------
# SAVE DATA
# -------------------------------------------------------------------
print("\n💾 Saving sentence-level data...")

# Export theme sentences to CSV
all_sentences = []
for theme, sentences in theme_sentences.items():
    for sent in sentences:
        all_sentences.append({
            'theme': theme,
            'voc_id': sent['voc_id'],
            'user_type': sent['user_type'],
            'category': sent['category'],
            'sentence_korean': sent['sentence_kor'],
            'sentence_english': sent['sentence_eng']
        })

sentences_df = pd.DataFrame(all_sentences)
sentences_df.to_csv(OUTPUT_DIR / "theme_sentences.csv", index=False, encoding='utf-8-sig')
print(f"✅ Saved: {OUTPUT_DIR}/theme_sentences.csv ({len(sentences_df)} sentences)")

# Export theme summary
theme_summary = pd.DataFrame([
    {'theme': theme, 'sentence_count': len(sentences)}
    for theme, sentences in theme_sentences.items()
]).sort_values('sentence_count', ascending=False)

theme_summary.to_csv(OUTPUT_DIR / "theme_summary.csv", index=False, encoding='utf-8-sig')
print(f"✅ Saved: {OUTPUT_DIR}/theme_summary.csv")

print("\n" + "="*80)
print("✅ VOC SENTENCE-LEVEL ANALYSIS COMPLETE!")
print("="*80)
print(f"\n📊 Summary:")
print(f"   • Processed {len(voc_df)} feedback entries")
print(f"   • Extracted {sum(len(row['sentences_kor']) for _, row in voc_df.iterrows())} total sentences")
print(f"   • Matched {len(all_sentences)} sentences to themes")
print(f"   • Generated interactive HTML report")
print(f"\n📁 All outputs saved to: {OUTPUT_DIR}/")
print(f"\n🌐 Open 'voc_analysis_interactive.html' to view the interactive report!")
print("\n" + "="*80 + "\n")
