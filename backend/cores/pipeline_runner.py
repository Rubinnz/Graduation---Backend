from backend.tools.tool_crawl_data import crawl_data
from backend.tools.tool_merge import merge_data
from backend.tools.tool_filter import filter_vietnam
from backend.tools.tool_sentiment import sentiment_classify
from backend.tools.tool_emotion import emotion_classify
from backend.tools.tool_topic import topic_extract

def execute_tool(tool, args=None):
    try:
        if tool == "crawl_data":
            return crawl_data()
        if tool == "merge_data":
            return merge_data()
        if tool == "filter_vietnam":
            return filter_vietnam()
        if tool == "sentiment_classify":
            return sentiment_classify()
        if tool == "emotion_classify":
            return emotion_classify()
        if tool == "topic_extract":
            return topic_extract()
        return "Unknown tool"
    except Exception as e:
        return f"❌ Error: {str(e)}"
