
from states.GameSession import GameSessionState 
from langgraph.graph import StateGraph,START, END

from graphs.util_nodes import get_user_input_node
from prompts.village_prompt import village_intro_prompt, village_user_input_analysis_prompt
# from prompts.village_prompt import village_look_around_RAG_prompt
from prompts.village_prompt import village_npc_choice_analysis_prompt, village_npc_persona_prompt
from prompts.village_prompt import village_other_question_prompt
from prompts.village_prompt import go_to_dungeon_prompt
from prompts.normal_prompt import explain_about_character
from llm.llm_setting import ChatModel
from tools.ragsystem import using_rag

# graph 시각화 내용
from IPython.display import Image, display
from PIL import Image as PILImage
import io

## node 정의 
def village_basic_question(state: GameSessionState) -> GameSessionState:
    character_state = state["character_state"]
    game_context = state["story_summary"]
    formatted_template = village_intro_prompt.invoke({
        "character_name": character_state["name"],
        "race": character_state["race"], 
        "class": character_state["profession"],
        "context": game_context
    })

    response = ChatModel.invoke(formatted_template)
    print(response.content)
    return {
        "system_messages":[response.content]
    }

def village_basic_question_repeat(state: GameSessionState) -> GameSessionState:
    print("""
다음 중에서 무엇을 원하시나요?
    1. 마을을 둘러보기 - 스톤브릿지의 각 구역을 탐험하며 마을의 분위기를 느껴봅니다
    2. 마을 주민과 대화하기 - 마을의 주요 인물들과 만나 정보를 수집하고 관계를 쌓습니다  
    3. 던전으로 떠나기 - 정화해야하는 던전으로 떠납니다. 
    4. 그외 - 직접 원하는 행동을 입력해주세요
          """)


def basic_question_analysis_router(state: GameSessionState) -> str:
    user_message = state["messages"][-1].content
    game_context = state["system_messages"][-1]

    formatted_template = village_user_input_analysis_prompt.invoke({
        "context": game_context,
        "user_input":user_message
    })

    result = ChatModel.invoke(formatted_template).content
    # "LOOKAROUND"
    if result == "LOOKAROUND":
        return result
    # "TALKING"
    elif result == "TALKING":
        print("""
마을에는 다음과 같은 주민들이 존재합니다. 
1. 마르쿠스 스톤브릿지 (촌장)
2. 소린 해머스트라이크 (대장장이)
3. 로즈마리 골든허스 (여관주인)
4. 가렌 스위프트블레이드 (길드마스터)
5. 아델라 라이트헨드 (치유사제) 
이 중에서 
            """)
        print("어떤 NPC와 대화를 나누고 싶으신가요?")
        return result
    # "STATUS"
    elif result == "STATUS":
        return result
    # "OTHER"
    elif result == "OTHER":
        return result
    # "GOTODUNGEON"
    elif result == "GOTODUNGEON":
        return result
    else:
        return "OTHER"




def describe_about_village(state: GameSessionState) -> GameSessionState:
    message = state["messages"][-1].content
    result = using_rag(message, "village")
    print(result)
    return state

def talking_npc_choice_analysis(state: GameSessionState) -> str:
    npc_name= ""
    user_input = state["messages"][-1].content
    game_context = state["game_context"]

    formatted_template = village_npc_choice_analysis_prompt.invoke({
        "context": game_context,
        "user_input": user_input
    })

    response = ChatModel.invoke(formatted_template)

    npc_name = response.content

    print(f"{npc_name}와 무슨 이야기를 나누고 싶으신가요?")

    return {
        "cache_box":{
            "npc_name": npc_name
        }
    }



def talking_like_npc(state: GameSessionState) -> GameSessionState:
    npc_name = state["cache_box"]["npc_name"]
    user_input = state["messages"][-1].content
    talking_context = state["talking_context"]
    game_context = state["game_context"]

    rag_content = using_rag(npc_name, "village")

    character_status = state["character_state"]
    user_name = character_status["name"]
    race = character_status["race"]
    profession = character_status["profession"]

    formatted_template = village_npc_persona_prompt.invoke({
        "npc_name": npc_name,
        "user_input": user_input,
        "rag_content": rag_content,
        "character_name": user_name,
        "talking_context": talking_context,
        "race": race,
        "context": game_context,
        "class": profession
    })

    response = ChatModel.invoke(formatted_template)
    print(response.content)

    return {
        "talking_context": response.content
    }

def explain_character_state(state: GameSessionState)-> GameSessionState:
    user_input = state["messages"][-1].content

    character_state = state["character_state"]

    game_context = state["game_context"]

    formatted_template = explain_about_character.invoke({
        "context": game_context,
        "status": character_state,
        "user_input": user_input
    })
    response = ChatModel(formatted_template)
    print(response.content)
    return state


def go_to_dungeon(state: GameSessionState) -> GameSessionState:
    system_message = state["system_messages"][-1]
    game_context = state["game_context"]
    talking_context = state["talking_context"]

    formatted_prompt =  go_to_dungeon_prompt.invoke({
        "system_messages": system_message,
        "game_context": game_context,
        "talking_context": talking_context
    })

    response = ChatModel.invoke(formatted_prompt)
    print(response.content)
    return state

def answer_to_other_question(state: GameSessionState) -> GameSessionState:
    user_input = state["messages"][-1].content
    game_context = state["game_context"]
    rag_content = using_rag(user_input, "village")

    formatted_template = village_other_question_prompt.invoke({
        "user_input": user_input,
        "game_context": game_context,
        "rag_content": rag_content
    })

    response = ChatModel.invoke(formatted_template)
    print(response.content)
    return {
        "system_messages": response.content
    }


##########

graph = StateGraph(GameSessionState)

## node 구성
# 기본 질문 노드 및 분석
graph.add_node("basic_question", village_basic_question)
graph.add_node("basic_question_repeat", village_basic_question_repeat)
graph.add_node("basic_question_input", get_user_input_node)
graph.add_node("basic_question_input_repeat", get_user_input_node)
graph.add_node("describe_village", describe_about_village)
graph.add_node("npc_choice_input", get_user_input_node)
graph.add_node("talking_npc_choice_analysis",talking_npc_choice_analysis)
graph.add_node("talking_to_npc",get_user_input_node)
graph.add_node("answer_like_npc", talking_like_npc)
graph.add_node("explain_about_character",explain_character_state)
graph.add_node("answer_to_other", answer_to_other_question)


# 던전으로 빠지기
graph.add_node("go_to_dungeon", go_to_dungeon)


graph.add_edge(START, "basic_question")
graph.add_edge("basic_question", "basic_question_input")
graph.add_conditional_edges(
    "basic_question_input",
    basic_question_analysis_router,
    {
        "LOOKAROUND": "describe_village",
        "TALKING": "npc_choice_input",
        "GOTODUNGEON": "go_to_dungeon",
        "OTHER": "answer_to_other",
        "STATUS": "explain_about_character"
    }
)
graph.add_edge("describe_village", "basic_question_repeat")
graph.add_edge("answer_to_other", "basic_question_repeat")
graph.add_edge("npc_choice_input","talking_npc_choice_analysis")
graph.add_edge("talking_npc_choice_analysis","talking_to_npc")
graph.add_edge("talking_to_npc","answer_like_npc")
graph.add_edge("answer_like_npc","basic_question_repeat")
graph.add_edge("explain_about_character","basic_question_repeat")
graph.add_edge("basic_question_repeat", "basic_question_input_repeat")
graph.add_conditional_edges(
    "basic_question_input_repeat",
    basic_question_analysis_router,
    {
        "LOOKAROUND": "describe_village",
        "TALKING": "npc_choice_input",
        "GOTODUNGEON": "go_to_dungeon",
        "OTHER": "answer_to_other",
        "STATUS": "explain_about_character" 
    }
)
graph.add_edge("go_to_dungeon",END)
    

result_village_graph = graph.compile()

def village_graph(initial_state: GameSessionState)-> GameSessionState: 
    try:
        result = result_village_graph.invoke(initial_state)
        return initial_state
    except Exception as e:
        print(f"Error during graph execution: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None 


if __name__== "__main__":
    try:
        png_graph = result_village_graph.get_graph().draw_mermaid_png()
        image = PILImage.open(io.BytesIO(png_graph))
        image.save("./village_langgraph.png")
    except Exception as e:
        print(f"PNG시각화 오류 :{e}")