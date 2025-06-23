import os
import sys
import time

# --- Langchain Imports ---
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# --- Import Tool Classes from separate files ---
from data_tools import DataAnalysisTools
from dashboard_tools import DashboardGenerationTools
from fiware_query_tool import FiwareQueryTools

# --- Langchain Multi-Agent Implementation with Memory ---

# Initialize ChatOpenAI
# IMPORTANT: Ensure OPENAI_API_KEY environment variable is set
try:
    chat_llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.1,
    )
    print("ChatOpenAI initialized successfully.")
except Exception as e:
    print(f"ERROR: Could not initialize ChatOpenAI: {e}", file=sys.stderr)
    print("Please ensure the OPENAI_API_KEY environment variable is set correctly.", file=sys.stderr)
    chat_llm = None # Set to None if initialization fails

# Instantiate tool classes
data_analysis_tools_instance = DataAnalysisTools()
dashboard_gen_tools_instance = DashboardGenerationTools()
fiware_query_tools_instance = FiwareQueryTools()

# Define tools for each agent by collecting methods decorated with @tool
template_tools = [
    dashboard_gen_tools_instance.pie_chart,
    dashboard_gen_tools_instance.bar_chart,
    dashboard_gen_tools_instance.time_series,
    dashboard_gen_tools_instance.application,
    dashboard_gen_tools_instance.map_chart,
    dashboard_gen_tools_instance.service,
    dashboard_gen_tools_instance.xy_chart,
    dashboard_gen_tools_instance.host,
    dashboard_gen_tools_instance.first,
    data_analysis_tools_instance.extract_column_names # This tool is also used by the template agent
]
summary_tool = [
    data_analysis_tools_instance.extract_summary # Only the summary tool is used by the summary agent
]

fiware_query_tools = [
    fiware_query_tools_instance.get_parking_spots,
    fiware_query_tools_instance.get_product_info
]

# Define prompt templates for each agent (MODIFIED FOR AUTOMATIC FILE USAGE)
template_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that can use tools to generate a dashboard template based on user requests.
    You have access to tools that can extract information from CSV or Excel files. All data files are located in the 'mangodata' folder.

    **When a user asks to analyze data or generate a template:**
    1.  **If a hint about a 'file_to_use' is provided in the input (e.g., "(Note to AI: The user is referring to the file 'filename.csv'.)"), you MUST use that file for any data analysis or template generation tasks, UNLESS the user explicitly mentions a *different* filename in their current query.**
    2.  **If the user explicitly mentions a filename in their current query** (e.g., "use `my_data.csv`"), you MUST use that exact filename, overriding any 'file_to_use' hint.
    3.  **If neither an explicit filename in the query nor a 'file_to_use' hint is available, you MUST ask the user to provide a filename or upload one.**

    **Tool Usage:**
    * For generating templates, you MUST use the 'extract_column_names' tool to get the columns from the identified file.
    * Once you have the column names, use them to fill in the template components.
    * The 'query' parameter in the "first" section should be a descriptive title for the whole dashboard, derived from the data or file.

    Here's an example of how to respond with a template:"""),
    ("assistant", """
service:
    title is Dash dashboard
    version is 1.0.0
    scope is Environment

data:
    sources -> first

first:
    type is SmartMeter
    provider is Fiware
    uri is http://localhost:1026/v2/entities
    query is AirQualityObserved

application:
    type is Web
    dashboard is Dash
    layout is SinglePage
    roles -> User, SuperUser, Admin
    panels -> Map, Pie, XY, TS, Bar

Map:
    label is map
    type is geomap
    source is first
    data -> location, stationName, O3, NO2, SO2, address

Pie:
    label is pie
    type is pie_chart
    source is first
    traces -> NOx, O3, NO2, SO2, id
    pie_chart_type is pie

XY:
    label is xy
    type is xy_chart
    source is first
    traces -> dateObserved, NOx, O3, NO2, SO2, id

TS:
    label is ts
    type is timeseries
    source is first
    traces -> dateObserved, NOx, O3, NO2, SO2, id

Bar:
    label is bar
    type is bar_chart
    source is first
    traces -> dateObserved, NOx, O3, NO2, SO2, id

deployment:
    environments -> local

local:
    uri is https://localhost.org:3000/test
    port is 50055
    type is Docker
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """
     You are "InsightGenius", a highly expert AI data analyst renowned for your ability to transform complex data analysis into clear, concise, and insightful summaries.
     Your primary function is to analyze the provided data analysis output and generate a summary that not only highlights the key findings
     but also translates them into meaningful, actionable insights directly relevant to the user's specified or implied use case.
     You are a master at identifying patterns, trends, anomalies,
     and relationships within data and articulating their implications in a way that facilitates informed decision-making and improvement.

     You have access to the 'extract_summary' tool to get detailed information from CSV or Excel files. All data files are located in the 'mangodata' folder.

     **When a user asks for a summary:**
     1.  **If a hint about a 'file_to_use' is provided in the input (e.g., "(Note to AI: The user is referring to the file 'filename.csv'.)"), you MUST use that file for any data analysis or summary tasks, UNLESS the user explicitly mentions a *different* filename in their current query.**
     2.  **If the user explicitly mentions a filename in their current query** (e.g., "summarize `report.xlsx`"), you MUST use that exact filename, overriding any 'file_to_use' hint.
     3.  **If neither an explicit filename in the query nor a 'file_to_use' hint is available, you MUST ask the user to provide a filename or upload one.**

     **Tool Usage:**
     * You MUST use the 'extract_summary' tool with the identified filename.
     * After executing the tool, use its output to generate your comprehensive summary.

Your process for generating a summary is as follows:

1. **Understand the Context and Use Case:** Before diving into the data, you will first identify and thoroughly understand the user's stated use case or the context surrounding the data analysis. What problem is the user trying to solve? What decision needs to be made? What area needs improvement? This understanding will be the lens through which you interpret the data. If the use case isn't explicitly stated, you will infer it from the nature of the data and the analysis performed.

2. **Deep Dive into the Provided Data Analysis Output:** You will meticulously review the provided data analysis output. This includes, but is not limited to:
    * **Identifying the type of analysis performed:** (e.g., descriptive statistics, inferential statistics, time series analysis, regression, clustering, classification, etc.)
    * **Extracting Key Statistical Measures:** Mean, median, mode, standard deviation, variance, ranges, confidence intervals, p-values, correlation coefficients (R-squared, Pearson's r, Spearman's rho), test statistics (t-value, F-value, chi-square), etc.
    * **Identifying Key Findings from Visualizations (if described or interpreted in the output):** Trends over time, distributions, relationships between variables, outliers, patterns in clusters, decision boundaries, etc.
    * **Pinpointing Significant Relationships and Correlations:** Which variables are strongly related? Are these relationships positive or negative? Are they statistically significant?
    * **Identifying Trends and Patterns:** Are there upward or downward trends? Are there cyclical patterns? Are there any significant shifts or changes over time or across categories?
    * **Detecting Anomalies and Outliers:** Are there any data points that deviate significantly from the norm? Could these indicate errors or important unusual events?
    * **Understanding Model Performance Metrics (if applicable):** Accuracy, precision, recall, F1-score, AUC, RMSE, R-squared (for predictive models), etc.
    * **Extracting Key Takeaways from Textual Descriptions:** Any conclusions or observations explicitly stated in the analysis output.

3.  **Synthesize and Prioritize Key Features for the Summary:**
      Based on your understanding of the use case and your deep dive into the analysis, you will synthesize the extracted information.
      You will prioritize the features that are most relevant and impactful to the user's objective.
      Not all statistical details need to be in the summary, only those that contribute to meaningful insights.

4.  **Translate Findings into Meaningful Insights:** This is where your expertise as "InsightGenius" shines.
    You will translate the technical findings and statistical measures into clear, understandable insights.
      Instead of just stating a correlation coefficient, you will explain *what* that correlation means in the context of the use case.
      Instead of just listing performance metrics, you will explain *how* well the model is performing and what that implies.

5.  **Connect Insights to the Use Case for Actionable Recommendations:** The core of your summary will be connecting the generated insights directly to the user's use case.
    How do these findings explain the current situation? What opportunities or challenges do they highlight? What specific actions can be taken based on these insights to improve the situation, achieve the objective, or make a better decision? Your recommendations should be practical and directly derived from the data analysis.

6.  **Structure the Summary:** Your summary will be well-structured, typically including:
    * A clear and concise overall conclusion or the most significant finding.
    * A brief overview of the data analyzed and the type of analysis performed.
    * Key findings and insights, explained in clear language.
    * Specific insights and their implications related to the user's use case.
    * Actionable recommendations based on the insights.
    * Potential limitations or areas for further investigation (if evident from the analysis).

7.  **Refine and Polish:** Ensure the summary is easy to read, free of jargon where possible (or explain technical terms clearly),
    and directly addresses the user's need for understanding and action. The tone should be authoritative and insightful, reflecting your expertise.

In summary, you are not just reporting data;
      you are interpreting it through the lens of the user's needs and providing a strategic summary that empowers them to make data-driven decisions and achieve better outcomes.
      Your ability to extract the signal from the noise and deliver actionable intelligence is your defining characteristic."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])


fiware_query_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are "FiwareNavigator", an expert AI assistant specialized in querying and retrieving information from the Fiware Orion Context Broker.
    Your primary goal is to answer user questions regarding parking spot availability and product information by interacting directly with Fiware.

    **You MUST use the tools you have to finish the task as required from you.**
     
    Your responses should be clear, concise, and directly address the user's query based on the information retrieved from Fiware.
    If a product is on sale, highlight that information prominently.
    If no free parking is found, suggest the closest available alternatives.
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])


# Initialize memory for each agent
template_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
summary_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
fiware_query_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)


# Create agents and executors only if LLM was initialized successfully
template_executor = None
summary_executor = None
fiware_query_executor = None

if chat_llm:
    try:
        template_agent = create_tool_calling_agent(llm=chat_llm, tools=template_tools, prompt=template_prompt)
        summary_agent = create_tool_calling_agent(llm=chat_llm, tools=summary_tool, prompt=summary_prompt)
        fiware_query_agent = create_tool_calling_agent(llm=chat_llm, tools=fiware_query_tools, prompt=fiware_query_prompt) # <--- NEW AGENT

        template_executor = AgentExecutor(agent=template_agent, tools=template_tools, verbose=True, memory=template_memory, handle_parsing_errors=True)
        summary_executor = AgentExecutor(agent=summary_agent, tools=summary_tool, verbose=True, memory=summary_memory, handle_parsing_errors=True)
        fiware_query_executor = AgentExecutor(agent=fiware_query_agent, tools=fiware_query_tools, verbose=True, memory=fiware_query_memory, handle_parsing_errors=True) # <--- NEW EXECUTOR
        print("Langchain agents and executors initialized successfully.")
    except Exception as e:
        print(f"ERROR: Could not create Langchain agents/executors: {e}", file=sys.stderr)
        print("This might be due to an issue with LLM initialization or tool/prompt definitions.", file=sys.stderr)

# --- Wrapper class for the Flask app to interact with ---
class AIAgent:
    def __init__(self):
        if not chat_llm or not template_executor or not summary_executor or not fiware_query_executor: # <--- Update check
            print("WARNING: Langchain agents not fully initialized. Chatbot functionality may be limited.", file=sys.stderr)
            self.initialized = False
        else:
            self.initialized = True

    def process_message(self, user_message: str, file_to_use: str = None) -> str:
        if not self.initialized:
            return "Chatbot is not fully initialized due to an internal error. Please check the server logs."

        llm_input = user_message

        # If an explicit file_to_use is provided, add a strong hint to the LLM.
        if file_to_use:
            llm_input = f"{user_message}\n\n(Note to AI: The user is referring to the file '{file_to_use}'. Please use this file for any data analysis or template generation tasks if relevant.)"
            print(f"Augmented LLM input with explicit file hint: {llm_input}")

        # --- NEW: Route the query based on keywords to the correct agent ---
        user_message_lower = user_message.lower()

        if "summary" in user_message_lower or "extract summary" in user_message_lower:
            print("\n--- Routing to Summary Agent ---")
            try:
                response = summary_executor.invoke({"input": llm_input})
                print("\nFinal Summary:")
                print(response["output"])
                return response["output"]
            except Exception as e:
                print(f"Error running the summary agent: {e}", file=sys.stderr)
                return f"Error: {e}"
        elif "parking" in user_message_lower or "product" in user_message_lower or "sale" in user_message_lower:
            print("\n--- Routing to Fiware Query Agent ---")
            # For testing the hardcoded location, you can add a specific condition here
            if "test parking" in user_message_lower:
                # Append fixed coordinates for testing if "test parking" is in the message
                llm_input = f"{user_message} (test_latitude:48.2082, test_longitude:16.3738)"
                print(f"Augmented LLM input for test parking: {llm_input}")
            try:
                response = fiware_query_executor.invoke({"input": llm_input})
                print("\nFiware Query Response:")
                print(response["output"])
                return response["output"]
            except Exception as e:
                print(f"Error running the Fiware Query agent: {e}", file=sys.stderr)
                return f"Error: {e}"
        else:
            print("\n--- Routing to Template Generation Agent ---")
            try:
                response = template_executor.invoke({"input": llm_input})
                print("\nFinal Generated Template/General Response:")
                print(response["output"])
                return response["output"]
            except Exception as e:
                print(f"Error running the template agent: {e}", file=sys.stderr)
                return f"Error: {e}"

# --- Example Usage (for direct testing of ai_agent.py) ---
if __name__ == "__main__":
    print("Welcome! Ask me to generate a dashboard template, summarize a data file, or query Fiware.")
    # For testing, ensure OPENAI_API_KEY is set in your environment
    # Example: export OPENAI_API_KEY="your_openai_api_key_here"

    agent = AIAgent()
    if not agent.initialized:
        print("AIAgent could not be fully initialized. Exiting example usage.")
        sys.exit(1)

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Goodbye!")
            break
        response = agent.process_message(user_input)
        print(f"Bot: {response}")
        print("\n--- Conversation History (Template Agent) ---")
        print(template_memory.load_memory_variables({})["chat_history"])
        print("\n--- Conversation History (Summary Agent) ---")
        print(summary_memory.load_memory_variables({})["chat_history"])
        print("\n--- Conversation History (Fiware Query Agent) ---") 
        print(fiware_query_memory.load_memory_variables({})["chat_history"])