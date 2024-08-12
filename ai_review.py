import requests


model = "HuggingFaceH4/zephyr-7b-beta"
# model = "justinlamlamlam/gpt350_chat_s_v0_1"
tokens = [
    "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",#qa account
    "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",#compnay account
    "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"# gregory account
]
API_URL = f"https://api-inference.huggingface.co/models/{model}"
def query(payload, headers):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def process_row(title, location, salary, description, client_requirements):
    target_title, target_location, target_industry, target_salary, previous_exp, resume, i_dont_have = client_requirements
    data = None
    # max_token_limit = 4096
    for token in tokens:
        headers = {"Authorization": f"Bearer {token}"} 
        
        data = query({
            "inputs": f"""Here are my job requirements:
                        Titles: {target_title}
                        Locations: {target_location}
                        Salary: greater than or equal to {target_salary}  
                        Industry: {target_industry}
                        Experience: {previous_exp}
                        Here is my resume: {resume}. And I don't have {i_dont_have}.

                        Now, analyze the given job details:

                        Title: {title}
                        Salary Range: {salary}
                        Description: {description}.
                        Does this job match my requirements? Please respond with "Yes" or "No" and provide a short explanation if necessary in less than 25 words in one sentence.""",
            "parameters": {
                        # "top_k": 50,
                        # "top_p": 0.9,
                        # "temperature": 0.7,
                        # "repetition_penalty": 1.2,
                        # "max_new_tokens": 1000,
                        # "max_time": 5.0,
                        "return_full_text": False,
            }
        }, headers)
        if 'error' in data and 'Rate limit' in data['error']:
                continue  # Try the next token
        else:
            break  # Break the loop if no error

    if data is None:
        comment = "Error: No valid response from Model"
    elif 'error' in data:
        comment = "Error: " + data['error']  # Get the actual error message
    else:
        comment = data[0]['generated_text'].strip()

    return comment