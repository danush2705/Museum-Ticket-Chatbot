# Museum Ticket Booking Chatbot

This project is a **Museum Ticket Booking Chatbot** hosted on Streamlit. It enables users to book and cancel museum tickets using a conversational interface. The chatbot interacts with a SQL database, hosted on Clever Cloud, to manage ticket availability, types, and user transactions. The chatbot interface is powered by **LangChain** and **ChatGroq**, making the user experience seamless and intuitive.

## Features
- **Book Tickets**: Users can ask the chatbot to book museum tickets based on availability, date, and ticket type.
- **Cancel Tickets**: Users can cancel previously booked tickets directly through the chatbot.
- **Database Connectivity**: The chatbot is connected to a SQL database (hosted on Clever Cloud) to handle real-time ticket booking and availability status.
- **Multi-lingual Support**: The chatbot supports multiple languages for a global user base (currently 8 languages).
- **Data Analytics**: The system also supports basic data analysis to track user trends and enhance the museum booking experience (optional).

## Technology Stack
- **Frontend**: [Streamlit](https://streamlit.io/) - used for hosting the chatbot interface.
- **Backend**:
  - **LangChain** and **ChatGroq** for natural language processing and chatbot functionalities.
  - **SQL Database** hosted on [Clever Cloud](https://www.clever-cloud.com/) for storing ticket and user data.
- **Cloud & APIs**:
  - **Azure API** for multi-language translation support.
  
## How to Run Locally

### Prerequisites
- [Python 3.8+](https://www.python.org/downloads/)
- [Streamlit](https://docs.streamlit.io/library/get-started/installation)
- [LangChain](https://github.com/hwchase17/langchain)
- [ChatGroq](https://www.groq.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/) (or your preferred SQL ORM)

### Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/museum-ticket-chatbot.git
   cd museum-ticket-chatbot
