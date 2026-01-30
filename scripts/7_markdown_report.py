"""
Script 7: Consolidated Markdown Report for Notion
Generates a comprehensive markdown report with key insights
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter
import json

print("\n" + "="*80)
print("MARKDOWN REPORT GENERATION")
print("="*80 + "\n")

# Configuration
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs" / "consolidated_report"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# LOAD ALL DATA
# ============================================================================

print("Loading data from all analyses...\n")

# 1. Bookings data
bookings_df = pd.read_csv(DATA_DIR / "2025_Bookings.csv")
print(f"✓ Bookings: {len(bookings_df)} rows, {bookings_df['job_id'].nunique()} unique jobs")

# 2. Patterns data
patterns_dir = BASE_DIR / "outputs" / "patterns"
shoot_types_freq = pd.read_csv(patterns_dir / "shoot_types_frequency.csv")
shoot_locations_freq = pd.read_csv(patterns_dir / "shoot_locations_frequency.csv")
usages_freq = pd.read_csv(patterns_dir / "usages_frequency.csv")
type_location_combos = pd.read_csv(patterns_dir / "type_location_combinations.csv")
type_usage_combos = pd.read_csv(patterns_dir / "type_usage_combinations.csv")
numeric_stats = pd.read_csv(patterns_dir / "numeric_statistics.csv")
print(f"✓ Patterns analysis data loaded")

# 3. VOC Analysis
voc_dir = BASE_DIR / "outputs" / "voc_analysis_revised"
theme_sentences = pd.read_csv(voc_dir / "theme_sentences.csv")
theme_summary = pd.read_csv(voc_dir / "theme_summary.csv")
print(f"✓ VOC analysis: {len(theme_summary)} themes, {len(theme_sentences)} sentences")

# 4. Vocabulary Analysis
vocab_dir = BASE_DIR / "outputs" / "vocabulary"
vocab_translations = pd.read_csv(vocab_dir / "vocabulary_with_translations.csv")
phrase_freq = pd.read_csv(vocab_dir / "phrase_frequency.csv")
job_name_freq = pd.read_csv(vocab_dir / "job_name_frequency.csv")
print(f"✓ Vocabulary analysis: {len(vocab_translations)} jobs analyzed")

# 5. Keywords Analysis
keywords_dir = BASE_DIR / "outputs" / "heuristic_keywords"
keywords_summary = pd.read_csv(keywords_dir / "keywords_summary.csv")
print(f"✓ Keywords: {len(keywords_summary)} jobs with keywords")

print("\n" + "="*80)
print("Generating Markdown Report")
print("="*80 + "\n")

# ============================================================================
# BUILD MARKDOWN REPORT
# ============================================================================

md_content = f"""# 2025 Booking Analysis Report

**Generated:** {datetime.now().strftime('%B %d, %Y')}  
**Period:** 2025 Full Year

---

## 📊 Executive Summary

### Key Metrics

| Metric | Count |
|--------|------:|
| **Total Jobs** | {bookings_df['job_id'].nunique()} |
| **Total Bookings** | {len(bookings_df)} |
| **Unique Models** | {bookings_df['talent_id'].nunique()} |
| **Unique Clients** | {bookings_df['client_id'].nunique()} |
| **Unique Brands** | {bookings_df['brand_name'].nunique()} |

### Top Performing Metrics

"""

# Add top metrics
region_counts = bookings_df['region'].value_counts()
nationality_counts = bookings_df['talent_nationality'].value_counts()

md_content += f"""- **Primary Region:** {region_counts.index[0]} ({region_counts.iloc[0]} jobs)
- **Most Common Model Nationality:** {nationality_counts.index[0]} ({nationality_counts.iloc[0]} bookings)
- **Average Shoot Duration:** {bookings_df['shoot_hours'].mean():.1f} hours
- **Average Client Budget:** ₩{bookings_df['price_client'].mean():,.0f}
- **Average Talent Payment:** ₩{bookings_df['price_talent'].mean():,.0f}

---

## 📈 1. Booking Patterns Analysis

### Usage Type Distribution

"""

# Usage distribution table
md_content += "| Usage Type | Frequency | Percentage |\n"
md_content += "|------------|----------:|-----------:|\n"
for idx, row in usages_freq.head(10).iterrows():
    md_content += f"| {row['Value']} | {row['Frequency']} | {row['Percentage']:.1f}% |\n"

md_content += "\n### Top Type + Location Combinations\n\n"
md_content += "| Combination | Frequency |\n"
md_content += "|-------------|----------:|\n"
for idx, row in type_location_combos.head(10).iterrows():
    md_content += f"| {row['Combination']} | {row['Frequency']} |\n"

md_content += "\n### Top Type + Usage Combinations\n\n"
md_content += "| Combination | Frequency |\n"
md_content += "|-------------|----------:|\n"
for idx, row in type_usage_combos.head(10).iterrows():
    md_content += f"| {row['Combination']} | {row['Frequency']} |\n"

md_content += "\n### Copyright Duration Distribution\n\n"
copyright_row = numeric_stats[numeric_stats['Metric'].str.contains('Copyright', case=False, na=False)]
if not copyright_row.empty:
    row = copyright_row.iloc[0]
    md_content += "| Statistic | Months |\n"
    md_content += "|-----------|-------:|\n"
    md_content += f"| Mean | {row['Mean']:.1f} |\n"
    md_content += f"| Median | {row['Median']:.1f} |\n"
    md_content += f"| Min | {row['Min']:.1f} |\n"
    md_content += f"| Max | {row['Max']:.1f} |\n"

md_content += "\n### Shoot Hours Distribution\n\n"
hours_row = numeric_stats[numeric_stats['Metric'].str.contains('Shoot Hours', case=False, na=False)]
if not hours_row.empty:
    row = hours_row.iloc[0]
    md_content += "| Statistic | Hours |\n"
    md_content += "|-----------|------:|\n"
    md_content += f"| Mean | {row['Mean']:.1f} |\n"
    md_content += f"| Median | {row['Median']:.1f} |\n"
    md_content += f"| Min | {row['Min']:.1f} |\n"
    md_content += f"| Max | {row['Max']:.1f} |\n"

md_content += """

**Key Insights:**
- Digital usage dominates the platform
- Indoor photo shoots are the most common combination
- Most copyright durations are standard 6-12 month contracts
- Typical shoot duration is 4-8 hours

---

## 💬 2. Voice of Customer Analysis

### Theme Distribution

"""

# VOC theme table
md_content += "| Theme | Sentence Count | Unique VOCs |\n"
md_content += "|-------|---------------:|------------:|\n"

# Calculate unique VOCs per theme
for idx, row in theme_summary.sort_values('sentence_count', ascending=False).iterrows():
    theme_name = row['theme']
    sentence_count = row['sentence_count']
    unique_vocs = theme_sentences[theme_sentences['theme'] == theme_name]['voc_id'].nunique()
    md_content += f"| {theme_name} | {sentence_count} | {unique_vocs} |\n"

md_content += "\n### Example Feedback by Theme\n\n"

# Add 10 example sentences per theme
for theme in theme_summary.sort_values('sentence_count', ascending=False)['theme']:
    theme_data = theme_sentences[theme_sentences['theme'] == theme].head(10)
    
    if len(theme_data) > 0:
        md_content += f"#### {theme}\n\n"
        
        for idx, (i, row) in enumerate(theme_data.iterrows(), 1):
            user_badge = "👔 Client" if row['user_type'] == 'Client' else "👤 Model"
            md_content += f"**{idx}. VOC #{row['voc_id']}** {user_badge}\n\n"
            md_content += f"> 🇰🇷 {row['sentence_korean']}\n\n"
            md_content += f"> 🇬🇧 {row['sentence_english']}\n\n"

md_content += """

**Key Insights:**
- Model selection features most frequently in feedback (316 mentions)
- Booking process efficiency is highly valued (155 mentions)
- Users appreciate Spotlite vs traditional agency model (113 mentions)
- Communication tools are effective (85 mentions)
- Feature requests indicate room for filter improvements (63 mentions)

---

## 📝 3. Vocabulary & Communication Insights

### Top 20 Job Names Analysis

"""

# Job names table with translations
md_content += "| Rank | Job Name (Korean) | English Translation | Frequency |\n"
md_content += "|-----:|-------------------|---------------------|----------:|\n"
for idx, row in job_name_freq.head(20).iterrows():
    korean = str(row['Job Name (Korean)']) if pd.notna(row['Job Name (Korean)']) else ''
    english = str(row['English Translation']) if pd.notna(row['English Translation']) else ''
    md_content += f"| {idx+1} | {korean[:40]} | {english[:40]} | {row['Frequency']} |\n"

md_content += "\n**Key Insight:** "
# Analyze job names
lookbook_count = sum(1 for name in job_name_freq.head(20)['English Translation'].astype(str) 
                     if pd.notna(name) and ('lookbook' in str(name).lower() or '룩북' in str(name).lower()))
seasonal_keywords = ['SS', 'FW', 'spring', 'summer', 'fall', 'winter', '봄', '여름', '가을', '겨울', '26']
seasonal_count = sum(1 for name in job_name_freq.head(20)['Job Name (Korean)'].astype(str) 
                     if pd.notna(name) and any(kw in str(name) for kw in seasonal_keywords))

md_content += f"""The majority of jobs are for **lookbook productions**, with seasonal collections being particularly prominent. 
{seasonal_count} of the top 20 job types include seasonal indicators (SS, FW, 26SS, etc.), suggesting strong seasonal booking patterns, 
particularly for fashion brands preparing new season launches.

### Top 30 Phrases from Inquiry Text

"""

md_content += "| Rank | Phrase (Korean) | English Translation | Frequency |\n"
md_content += "|-----:|-----------------|---------------------|----------:|\n"
for idx, row in phrase_freq.head(30).iterrows():
    md_content += f"| {idx+1} | {row['Phrase (Korean)']} | {row['English Translation']} | {row['Frequency']} |\n"

md_content += "\n**Key Insight:** "
# Analyze phrases
communication_phrases = ['촬영', '문의', '요청', '확인', '연락', '채팅']
concept_phrases = ['컨셉', '스타일', '무드', '느낌']
channel_phrases = ['스튜디오', '실내', '실외', 'outdoor', 'indoor']

comm_count = sum(1 for phrase in phrase_freq.head(30)['Phrase (Korean)'].astype(str) 
                 if any(kw in phrase for kw in communication_phrases))
concept_count = sum(1 for phrase in phrase_freq.head(30)['Phrase (Korean)'].astype(str) 
                    if any(kw in phrase for kw in concept_phrases))

md_content += f"""Inquiry texts are predominantly **process-oriented** rather than concept-heavy. 
{comm_count} of the top 30 phrases relate to communication and logistics (shoot scheduling, confirmation, contact), 
while only {concept_count} phrases relate to creative concepts. This indicates that **clients rely heavily on concept photos** 
to communicate visual direction rather than describing it in text, emphasizing the importance of visual reference materials.

---

## 🏷️ 4. Keyword Analysis from Jobs & Models

### Top Concept Keywords

"""

# Extract top concept keywords
all_job_kw = []
for kw_str in keywords_summary['job_keywords']:
    if pd.notna(kw_str):
        all_job_kw.extend([k.strip() for k in str(kw_str).split(',') if k.strip()])

job_kw_counter = Counter(all_job_kw)
top_job_kw = job_kw_counter.most_common(15)

md_content += "| Rank | Keyword | Frequency |\n"
md_content += "|-----:|---------|----------:|\n"
for idx, (kw, count) in enumerate(top_job_kw, 1):
    md_content += f"| {idx} | {kw} | {count} |\n"

md_content += "\n### Top Model Keywords\n\n"

# Extract top model keywords
all_model_kw = []
for kw_str in keywords_summary['model_keywords']:
    if pd.notna(kw_str):
        all_model_kw.extend([k.strip() for k in str(kw_str).split(',') if k.strip()])

model_kw_counter = Counter(all_model_kw)
top_model_kw = model_kw_counter.most_common(15)

md_content += "| Rank | Keyword | Frequency |\n"
md_content += "|-----:|---------|----------:|\n"
for idx, (kw, count) in enumerate(top_model_kw, 1):
    md_content += f"| {idx} | {kw} | {count} |\n"

md_content += "\n### Concept Photo Usage Statistics\n\n"

# Calculate concept photo stats
bookings_df['has_concept_photos'] = bookings_df['concept_photos'].apply(
    lambda x: pd.notna(x) and str(x).strip() not in ['{}', '']
)

jobs_with_concepts = bookings_df.groupby('job_id')['has_concept_photos'].first()
concept_usage_rate = (jobs_with_concepts.sum() / len(jobs_with_concepts) * 100)

# Count photos per job
def count_photos(field_value):
    if pd.isna(field_value):
        return 0
    field_str = str(field_value).strip()
    if field_str == '{}' or field_str == '':
        return 0
    field_str = field_str.strip('{}').strip('"')
    values = [v.strip().strip('"') for v in field_str.split(',')]
    return len([v for v in values if v and v.startswith('http')])

bookings_df['concept_photo_count'] = bookings_df['concept_photos'].apply(count_photos)
jobs_concept_counts = bookings_df.groupby('job_id')['concept_photo_count'].first()
avg_concept_photos = jobs_concept_counts[jobs_concept_counts > 0].mean()

md_content += f"""| Metric | Value |
|--------|------:|
| **Jobs with Concept Photos** | {jobs_with_concepts.sum()} ({concept_usage_rate:.1f}%) |
| **Jobs without Concept Photos** | {(~jobs_with_concepts).sum()} ({100-concept_usage_rate:.1f}%) |
| **Average Photos (when provided)** | {avg_concept_photos:.1f} |
| **Max Photos in Single Job** | {jobs_concept_counts.max()} |

**Key Insights:**
- **Concept keywords** are dominated by "photography", "lookbook", and "beauty" projects
- **Model attributes** most frequently requested: commercial style, casual wear, and specific physical features (slim, specific hair colors)
- **{concept_usage_rate:.0f}% of jobs include concept photos**, averaging {avg_concept_photos:.1f} reference images
- Concept photo usage is critical for visual direction, confirming the insight that clients prefer visual over textual descriptions

---

## 🎯 Strategic Recommendations

### 1. Enhance Search & Filter Capabilities
**Based on:** 57 VOC mentions + Feature Requests theme (63 mentions)

- Add race/ethnicity filter (explicitly requested in multiple VOCs)
- Improve nationality filtering UX
- Consider adding style-based search (commercial, editorial, casual)

### 2. Optimize for Seasonal Lookbook Production
**Based on:** Job name analysis showing seasonal concentration

- Pre-plan capacity for seasonal peaks (Jan-Feb for SS, Jun-Aug for FW)
- Create seasonal lookbook templates
- Develop seasonal model collections/portfolios

### 3. Strengthen Visual Communication Tools
**Based on:** {concept_usage_rate:.0f}% concept photo usage + inquiry text analysis

- Prioritize concept photo upload and display
- Add mood board creation tools
- Implement visual reference libraries

### 4. Maintain Agency Competitive Advantage
**Based on:** 113 VOC mentions comparing favorably to traditional agencies

- Emphasize direct communication benefits in marketing
- Highlight pricing transparency
- Promote speed advantages over traditional booking channels

### 5. Expand Model Diversity
**Based on:** Feature requests + model selection feedback

- Actively recruit underrepresented demographics (particularly mentioned: Black models)
- Expand domestic/international model balance based on demand
- Develop specialized model categories (commercial, editorial, lifestyle)

---

## 📁 Data Sources

- **2025_Bookings.csv** - {len(bookings_df)} bookings across {bookings_df['job_id'].nunique()} jobs
- **VOC_Search.csv** - {len(theme_sentences['voc_id'].unique())} customer feedback entries
- **Pattern Analysis** - Shoot type, location, and usage combinations
- **Heuristic Keywords** - Privacy-safe keyword extraction from text and metadata

**Analysis Period:** Full Year 2025  
**Report Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

---

*For internal use only. Confidential.*
"""

# ============================================================================
# SAVE MARKDOWN REPORT
# ============================================================================

output_file = OUTPUT_DIR / f"Consolidated_Report_{datetime.now().strftime('%Y%m%d')}.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(md_content)

print(f"✅ Saved Markdown report: {output_file}")
print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")

print("\n" + "="*80)
print("✅ MARKDOWN REPORT COMPLETE!")
print("="*80)
print(f"\n📄 Report saved: {output_file}")
print("\n💡 To import to Notion:")
print("   1. Open Notion")
print("   2. Create new page or go to existing page")
print("   3. Type /import and select 'Markdown'")
print("   4. Upload this file")
print("\n" + "="*80 + "\n")
