import os
import argparse
from openai import OpenAI

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, required=True, help='Path to transcript file')
parser.add_argument('--output', type=str, required=True, help='Path to output markdown file')
parser.add_argument('--video_id', type=str, required=True, help='YouTube video ID')
parser.add_argument('--superhuman', action='store_true', help='Enable superhuman AI capabilities')
args = parser.parse_args()

with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
    transcript = f.read()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Enhanced superhuman prompt when superhuman mode is enabled
if args.superhuman:
    instructions = (
        f"You are a superhuman multimodal AI with advanced reasoning capabilities. "
        f"Analyze this YouTube video transcript (ID: {args.video_id}) with the following enhanced abilities:\n\n"
        f"🧠 ADVANCED REASONING: Apply deep cognitive analysis and critical thinking\n"
        f"🎯 MULTI-PERSPECTIVE ANALYSIS: Consider multiple viewpoints and interpretations\n"
        f"📊 STRUCTURED INSIGHTS: Extract key themes, arguments, and evidence systematically\n"
        f"🔍 FACT-CHECK AWARENESS: Identify claims that could be verified\n"
        f"📈 EMOTIONAL INTELLIGENCE: Analyze sentiment, tone, and emotional undertones\n"
        f"💡 INNOVATIVE CONNECTIONS: Draw novel insights and cross-domain connections\n"
        f"🎭 CONTEXTUAL UNDERSTANDING: Consider cultural, historical, and situational context\n\n"
        f"Create a comprehensive markdown summary with:\n"
        f"- Clear, engaging title with video ID ({args.video_id})\n"
        f"- Executive summary for quick understanding\n"
        f"- Detailed analysis with multiple perspectives\n"
        f"- Key insights and novel connections\n"
        f"- Actionable takeaways and recommendations\n"
        f"- Critical evaluation of arguments and evidence\n"
        f"- Emotional tone and sentiment analysis\n"
        f"Use emojis strategically to enhance readability. Output only the summary."
    )
else:
    instructions = (
        f"You are a helpful assistant skilled at summarizing YouTube transcripts. "
        f"Summarize the provided transcript in markdown format as detailed as possible, "
        f"using relevant emojis to enhance readability. "
        f"Start with a clear, engaging title that incorporates the video ID ({args.video_id}). "
        f"Structure the summary with appropriate headings, bullet points, or numbered lists. "
        f"Do NOT include any explanations or comments before or after the summary; "
        f"only output the summary itself. Summarize in the language of the transcript."
    )

try:
    response = client.responses.create(
        model="gpt-4-turbo" if args.superhuman else "gpt-4-mini",
        instructions=instructions,
        input=transcript,
        max_output_tokens=4000 if args.superhuman else 3000
    )
    
    summary_content = response.output_text
    
    # Add superhuman AI signature if enabled
    if args.superhuman:
        summary_content += "\n\n---\n\n*🤖 This analysis was generated using superhuman AI capabilities with advanced reasoning, multi-perspective analysis, and comprehensive content understanding.*"

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(summary_content)
        
    print(f"✅ Summary generated successfully using {'superhuman AI' if args.superhuman else 'standard AI'} capabilities")
    
except Exception as e:
    print(f"❌ Error generating summary: {e}")
    # Fallback: create a basic summary
    fallback_summary = f"""
# Summary of Video {args.video_id}

## Content Overview
- **Video ID**: {args.video_id}
- **Content Length**: {len(transcript.split())} words
- **Analysis Status**: Fallback mode (API unavailable)

## Basic Insights
- Video contains substantial content for analysis
- Estimated {len(transcript.split()) / 150:.1f} minutes of reading time
- Content appears to be informational in nature

## Note
Full AI analysis was not available. Please check your OpenAI API key and try again for detailed insights.

---
*Generated in fallback mode*
"""
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(fallback_summary)
    
    print("⚠️ Used fallback summary generation")