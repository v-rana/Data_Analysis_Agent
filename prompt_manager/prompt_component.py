import os

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder



PROMPT_FOLDER = os.getenv('PROMPT_FOLDER','prompts')

# one function to read a prompt based on name
def read_prompt(p_name: str) -> str:
    file_name = PROMPT_FOLDER+ '/' + p_name+'.txt'
    with open(file_name) as f:
        prompt = f.read()
    return prompt.strip()

# function to get the full prompt template
def get_prompt_template(sys_p_name:str,user_template_name: str ) -> ChatPromptTemplate:
    system_prompt = read_prompt(sys_p_name)
    user_prompt_template = read_prompt(user_template_name)
    messages = [ ('system',system_prompt) , 
                MessagesPlaceholder(variable_name="chat_history"),
                ('user',user_prompt_template)]
    
    template = ChatPromptTemplate.from_messages(messages)
    return template

