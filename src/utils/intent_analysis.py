from langchain_core.messages import HumanMessage
from prompts.normal_prompt import user_input_analysis_to_positive_or_negative
from llm.llm_setting import ChatModel

import inspect

def classify_intent(message: str) -> str:
    """간단한 의도 분류"""
    text = message.content.lower().strip()

    formatted_template = user_input_analysis_to_positive_or_negative.invoke({
        "user_input": text
    })

    response = ChatModel.invoke(formatted_template)

    
    # 긍정적 응답
    if response.content == "POSITIVE":
        return "POSITIVE"
    # 부정적 응답  
    elif response.content == "NEGATIVE":
        return "NEGATIVE"
    else:
        return "NEGATIVE"
