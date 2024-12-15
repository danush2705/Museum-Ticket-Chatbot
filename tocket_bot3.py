import os
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.chat_history import InMemoryChatMessageHistory
import re
from datetime import datetime
import streamlit as st

# Initialize the LLM
llm = ChatGroq(
    temperature=0,
    groq_api_key="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",
    model="llama3-70b-8192",
)

#, "pool_size": 100,"pool_recycle": 3600, "pool_pre_ping": True

import traceback

def connect():
    try:
        mysql_uri = (
            'mysql+mysqlconnector://u9fo9wetp3yfgvwc:WV98kfOrEsxmrZ3m84rB@'
            'bz3as303uii27wd8fhxb-mysql.services.clever-cloud.com:3306/bz3as303uii27wd8fhxb'
        )
        db = SQLDatabase.from_uri(mysql_uri, engine_args={"connect_args": {"connect_timeout": 3600}}) 
        return mysql_uri, db

    except Exception as e:
        st.error(f"Database connection error: {e}")
        print(f"Exception in connect: {e}")
        traceback.print_exc()  # This will give you a more detailed traceback
        return None, None  # Return None if connection fails

mysql_uri, db = connect()

def get_schema(_):
    try:
        schema = db.get_table_info()
        return schema
    except Exception as e:
        st.error(f"Error fetching schema: {e}")
        print(f"Exception in get_schema: {e}")
        return None  # Return None if schema fetching fails

def generate_sql_query(template, question, schema):
    sql_query = template.format(schema=schema, question=question)

    sql_query_lines = sql_query.strip().split("\n")

    if len(sql_query_lines) > 1:
        sql_query = sql_query_lines[-1].strip()      

    if sql_query is None:
        st.error("No Query Generated")

    return sql_query

#user_question = "Book me a ticket for 3rd November 2024 at 3 pm to 5pm.Name is Ram and ticket type is Indian adult"


def remove_ordinal_suffix(date_str):
    # Remove ordinal suffixes (st, nd, rd, th) from the date string
    return re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', date_str)

def extract_user_inputs(question):
    # Define refined patterns for extracting user inputs
    patterns = {
        "name": r'(?:under the name|name\s*is)\s+([\w\s]+?)(?: for|$)',
        "phone_number": r'contact(?:\s*number)?\s*is\s*(\+?\d[\d\s\-]+)',
        "museum_name": r'\b(?:for|to)\s+(?:the\s+)?([\w\s]+museum)\b', 
        "tickets": r'book\s+me\s+(\d+)\s+tickets?',
        "ticket_type": r'the\s+ticket\s+type\s+is\s+(indian adult|indian|foreign|child|adult)',
        "from_time": r'from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
        "end_time": r'until\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
        "date": r'\b(?:on\s*)?(\d{1,2}(?:st|nd|rd|th)?(?:\s+(?:January|February|March|April|May|June|July|August|September|October|November|December))?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'
    }
    
    input_data = {}

    # Extract information using regex patterns
    for key, pattern in patterns.items():
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            input_data[key] = match.group(1).strip()
            print(f"Pattern for {key} matched: {match.group(1)}")
        else:
            input_data[key] = None
            print(f"No match for pattern: {pattern} in question: {question}")

    # Convert time to consistent 24-hour format
    for key in ['from_time', 'end_time']:
        if input_data[key]:
            time_str = input_data[key].replace('.', ':').strip()
            try:
                input_data[key] = datetime.strptime(time_str, '%I:%M %p').strftime('%H:%M')
            except ValueError:
                try:
                    input_data[key] = datetime.strptime(time_str, '%I %p').strftime('%H:%M')
                except ValueError:
                    input_data[key] = None

    # Convert date to consistent YYYY-MM-DD format
    if input_data["date"]:
        try:
            date_str = remove_ordinal_suffix(input_data["date"])  # Remove ordinal suffix
            input_data["date"] = datetime.strptime(date_str, '%d %B %Y').strftime('%Y-%m-%d')
        except ValueError:
            try:
                input_data["date"] = datetime.strptime(date_str, '%d/%m/%Y').strftime('%Y-%m-%d')  # Handle date in format d/m/Y
            except ValueError:
                input_data["date"] = None

    return input_data

# Store chat history across sessions
store = {}  # memory is maintained outside the chain

# Get chat history for a specific session
def get_session_history(session_id: str, store) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

def extract_sql_queries(text):
    pattern = re.compile(r"""
        (?:SELECT|INSERT|UPDATE|DELETE|CREATE\s+TABLE|DROP\s+TABLE|ALTER\s+TABLE|TRUNCATE|
        PRAGMA|COPY|GRANT|REVOKE|COMMENT|ANALYZE|VACUUM|CLUSTER|DISCARD|EXPLAIN|LISTEN|NOTIFY|
        UNLISTEN|SET|RESET|SHOW|START\s+TRANSACTION|BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|
        PREPARE|EXECUTE|DEALLOCATE|DECLARE|FETCH|MOVE|CLOSE|DO|REINDEX|REFRESH\s+MATERIALIZED\s+VIEW|
        CREATE\s+EXTENSION|DROP\s+EXTENSION|CREATE\s+SCHEMA|DROP\s+SCHEMA|CREATE\s+SEQUENCE|DROP\s+SEQUENCE|
        CREATE\s+INDEX|DROP\s+INDEX|CREATE\s+VIEW|DROP\s+VIEW|CREATE\s+FUNCTION|DROP\s+FUNCTION|
        CREATE\s+TRIGGER|DROP\s+TRIGGER|CREATE\s+RULE|DROP\s+RULE|CREATE\s+AGGREGATE|DROP\s+AGGREGATE|
        CREATE\s+TYPE|DROP\s+TYPE|CREATE\s+DOMAIN|DROP\s+DOMAIN|CREATE\s+OPERATOR|DROP\s+OPERATOR|
        CREATE\s+LANGUAGE|DROP\s+LANGUAGE|CREATE\s+TEXT\s+SEARCH\s+CONFIGURATION|DROP\s+TEXT\s+SEARCH\s+CONFIGURATION|
        CREATE\s+TEXT\s+SEARCH\s+DICTIONARY|DROP\s+TEXT\s+SEARCH\s+DICTIONARY|CREATE\s+TEXT\s+SEARCH\s+PARSER|
        DROP\s+TEXT\s+SEARCH\s+PARSER|CREATE\s+TEXT\s+SEARCH\s+TEMPLATE|DROP\s+TEXT\s+SEARCH\s+TEMPLATE|
        CREATE\s+TABLESPACE|DROP\s+TABLESPACE|CREATE\s+USER\s+MAPPING|DROP\s+USER\s+MAPPING|
        CREATE\s+FOREIGN\s+TABLE|DROP\s+FOREIGN\s+TABLE|CREATE\s+SERVER|DROP\s+SERVER|CREATE\s+FOREIGN\s+DATA\s+WRAPPER|
        DROP\s+FOREIGN\s+DATA\s+WRAPPER|IMPORT\s+FOREIGN\s+SCHEMA|CREATE\s+PUBLICATION|DROP\s+PUBLICATION|
        CREATE\s+SUBSCRIPTION|DROP\s+SUBSCRIPTION|CREATE\s+TRANSFORM|DROP\s+TRANSFORM)\b.*?;   
    """, re.IGNORECASE | re.DOTALL | re.VERBOSE)
    
    matches = pattern.findall(text)
    return matches if matches else []

# Chain for checking if inputs are missing
def check_missing_inputs(user_inputs):
    required_inputs = ["name", "phone_number", "museum_name", "tickets", "ticket_type", "from_time", "end_time", "date"]
    missing_inputs = [key for key in required_inputs if user_inputs.get(key) is None]
    return missing_inputs

# Ask for missing details
def ask_for_missing_details(missing_inputs):
    if missing_inputs:
        questions = {
            "name": "Please provide your name.",
            "phone_number": "What is your phone number?",
            "museum_name": "Which museum would you like to visit?",
            "tickets": "How many tickets do you need?",
            "ticket_type": "What type of ticket do you want (adult/child/foreign/indian)?",
            "from_time": "What is your preferred start time for the visit?",
            "end_time": "When do you plan to leave?",
            "date": "What date would you like to visit the museum?"
        }
        prompts = [questions[input_name] for input_name in missing_inputs]
        return "I still need: " + " ".join(prompts)
    return None




def bot_Start(user_question):

    template = """You are a MySQL expert.Never miss the column 'no_of_tickets' for the table UserData.For all tables never miss to fill the columns with the details.'payment_id' (an auto incremented column representing the unique ID generated for each payment) Never let a column be NULL.Get 'ticket_no' column for the availability table using the 'id' column from UserData.To use id for the table UserData use the column phone number to access the id of the user.To use the column Museum_ID use the column Museum_Name to get the column Museum_ID. Always generate the code only and do not generate any other text. Do not generate step-by-step MySQL code. Just generate the final codes alone. When generating SQL queries, ensure that no column is ever set to NULL. Every column in every table must have a valid and appropriate value. Pay special attention to maintaining strict foreign key relationships throughout the database. For instance, the ticket_no in the PaymentDetails table must always correspond to a valid Ticket_ID in the Tickets table. 
    Ensure that no integrity errors occur when establishing these relationships. Additionally, never assume or guess table or column names; always use the exact names provided in the database schema descriptions. It is crucial that every SQL query references the correct tables and columns without any omissions or errors. The chatbot should only handle operations related to booking a ticket, canceling a ticket, or viewing ticket details. If any other operations are requested, the chatbot should politely inform the user that the process cannot be executed and inquire if anything else can be done.
    When booking a ticket, ensure that the availability in the Availability table is updated accurately by reducing it according to the number of tickets purchased. Finally, always ensure that every generated query is perfect and free of errors, particularly those related to foreign keys and data integrity. 
    The below lines represent the details of the tables. Use these table details to print the accurate MySQL code.
    Availability: This table focuses on displaying ticket availability details, showing whether the tickets are available for purchase, the cost of the ticket, and the type of ticket. It includes the following columns: 'ticket_no' (an integer column representing the unique ID of a ticket which is an auto incrementing column), 'type_of_ticket' (a column representing the type of ticket, such as adult, child, foreign, or Indian), 'availability' (a column representing the number of tickets available for a particular time at the museum), and 'cost' (a column representing the cost of the ticket).
    Museums: This table contains details about the museums, with columns including 'Museum_ID' (an integer column representing the unique ID of the museum which is an auto generating column), 'Museum_Name' (a column representing the name of the museum),To use Museum_ID use the Museum_Name to get the Museum_ID. 'Museum_Address' (a column representing the address of the museum), 'Current_Status' (a column representing whether the museum is currently open or closed), 'Opening_Time' (a column representing the time the museum opens), and 'Closing_Time' (a column representing the time the museum closes).
    PaymentDetails: This table represents payment details for tickets purchased and includes the following columns: 'ticket_no' (a column representing the ticket number, used as a foreign key referencing the Availability table), 'payment_id' (an auto incremented column representing the unique ID generated for each payment), 'payment_method' (a column representing the method by which the payment was made, such as Credit Card or PayPal), and 'payment_date' (a column representing the date and time when the payment was completed).
    Tickets: This table contains details of the tickets issued for museum visits, with columns including 'Ticket_ID' (an auto-incremented integer column representing the unique ID of the ticket), 'Ticket_Date' (a column representing the date the ticket is issued), 'Museum_ID' (a column representing the ID of the museum, used as a foreign key referencing the Museums table), 'Activity_Status' (a column representing the status of the ticket, such as Active or Cancelled), and 'id' (a column representing the user ID, used as a foreign key referencing the UserData table).
    UserData: This table contains details about the users who purchase tickets, with columns including 'id' (an auto-incremented integer column representing the unique ID of the user), 'name' (a column representing the name of the user), 'no_of_tickets' (a column representing the number of tickets bought by the user), 'event_datetime' (a column representing the date and time when the event for the ticket is scheduled), 'intime' (a column representing the time when the user can enter the museum), 'outtime' (a column representing the time when the user should exit the museum), 'phone_number' (a column representing the user's phone number), and 'email_id' (a column representing the user's email address).
    Use this template to guide your chatbot in generating accurate and simple MySQL queries based on the provided descriptions without any assumptions.
    Question: {question}
    SQL Query:"""

    prompt = ChatPromptTemplate.from_template(template)
    schema = get_schema(None)

    sql_query = generate_sql_query(template, user_question, schema)

    sql_chain = (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )

    sql_query = sql_chain.invoke({"question": user_question})

    filtered_sql_queries = extract_sql_queries(sql_query)    

    return filtered_sql_queries


db = SQLDatabase.from_uri(mysql_uri, engine_args={"connect_args": {"connect_timeout": 3600}}) 

def run_queries(sql_queries):
    results = []
    try:
        for query in sql_queries:
            result = db.run(query)
            results.append(result)
        return results
    
    except Exception as e:
        st.error(f"Error executing SQL queries: {e}")
        print(f"Exception in run_queries: {e}")
        return None  # Return None if there's an error

def bot_End(u_question, sql_queries):
    # Response generation template
    template_response = """
    Based on the question, SQL query, and SQL response, write a full natural language response.
    Print the 'ticket_no' as ticket number for each ticket that we book.
    Question: {question}
    SQL Query: {query}
    SQL Response: {response}
    """

    prompt_response = ChatPromptTemplate.from_template(template_response)

   

    try:
        # Full chain for generating final natural language response
        full_chain = (
        RunnablePassthrough.assign(query=lambda vars:sql_queries )  # Assuming sql_query is the full text containing multiple queries
        .assign(
            schema=get_schema,
            response=lambda vars: run_queries(vars["query"]),  # Running the list of queries
        )
        | prompt_response
        | llm
        )

    except Exception as e:
        st.error(e)

    final_msg=full_chain.invoke({"question": u_question})

    return final_msg.content


def booking_chain(chat_history, user_question, user_inputs):

    chat_history.add_user_message(user_question)

    # Extract user inputs
    inputs_extracted = extract_user_inputs(user_question)
    
    # Update inputs with any new ones extracted from the current user input
    user_inputs.update({key: value for key, value in inputs_extracted.items() if value})

    # Check for missing inputs
    missing_inputs = check_missing_inputs(user_inputs)

    if missing_inputs:
        # Ask only for missing inputs
        missing_prompt = ask_for_missing_details(missing_inputs)
        chat_history.add_ai_message(missing_prompt)

        return missing_prompt, user_inputs, 0
        
    else:
        # All required inputs are now gathered, generate the final question string safely
        user_question_with_inputs = (
        f"Book {user_inputs.get('tickets', 'N/A')} tickets for {user_inputs.get('name', 'N/A')} "
        f"(phone number: {user_inputs.get('phone_number', 'N/A')}) on {user_inputs.get('date', 'N/A')} "
        f"from {user_inputs.get('from_time', 'N/A')} until {user_inputs.get('end_time', 'N/A')} "
        f"for {user_inputs.get('ticket_type', 'N/A')} tickets at {user_inputs.get('museum_name', 'N/A')}."
    )
        print(f"Proceeding with query: {user_question_with_inputs}")

        return user_question_with_inputs, user_inputs, 1

# Initialize conversation with session ID
def start_conversation(session_id):
    print(f"Starting conversation for session: {session_id}")
    booking_chain(session_id)

#book me 1 ticket under the name Pandit for National Museum on 18th September 2024 from 3 pm until 6 pm and contact number is 6850503223 and the ticket type is indian adult.
