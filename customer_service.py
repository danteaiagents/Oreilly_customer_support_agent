from langchain.tools import tool
from langchain_openai.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.messages.tool import ToolMessage
from langgraph.graph import StateGraph

# Define our single business tool
def cancel_order(order_id: str) -> str:
    """Cancel an order that hasn't shipped"""
    # Assume the API to cancel order is called here
    return f"Order {order_id } has been cancelled "
    
# Agent brain. Invoke LLM, run tool then invoke llm again
def call_model(state):
    msgs = state["messages"]
    order = state.get("order", {"order_id": "UNKNOWN"})
    # System prompt tells model exactly what to do
    
    prompt = (f'''
      You are an ecommerce support agent.
      ORDER ID: {order['order_id']}
      if the customer asks to cancel, call cancel_order(order_id)
      and then send a simple confirmation otherwise just respond normally.''')
    
    full = [SystemMessage(prompt)] + msgs
    
    #first LLM Pass: Decide whether to call our tool
    AIMessage = ChatOpenAI(model="gpt-5", temparature=0)(full)
    out = [first]
    
    if getattr(first, "tool_calls", None):
        #run the cancel order tool
        tc = first.tools_calls[0]
        result = cancel_order(**tc["args"])
        out.append(ToolMessage(content=result, tool_call_id=tc['id']))
        
        # 2nd LLM Pass: Generate the final confirmation text
        AIMessage = ChatOpenAI(model="gpt-5", temparature=0)(full)
        
        return {"messages": out}
    
# Wire it all up in stategrapm
def construct_graph():
    g = StateGraph({"order": None, "messages": []})
    g.add_node("assistant", call_model)
    g.set_entry_point("assistant")
    return g.compile

graph = construct_graph()

if __name__ == '__main__':
    example_order = {'order_id': 'A12345'}
    convo = [HumanMessage(content="Please cancel my order A12345.")]
    result = graph.invoke({"order": example_order, "messages": convo})
    
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")