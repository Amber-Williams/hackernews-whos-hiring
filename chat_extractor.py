import json

import openai

openai.api_key = "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"


class ChatExtractor:
    def __init__(self, model="gpt-3.5-turbo"):
        self.model = model
        self.system_role = """You are an assistant that extracts the key points of a job posting
      
        Instructions:
            - Be concise and only include key points of salary, location, remote/on-onsite, company name, company location, link to apply, languages and frameworks
            - Use lowercase,
            - Don't use line breaks.
            - If it isn't an comment for a company hiring, then return empty output.
            - If there isn't a salary mentioned, then return empty output.
            - Provide the mapping in a Python dictionary format for easier readability.
            - Ensure to return JSON parsable output."""
        self.example_text_1 = """
            Figma | https://www.figma.com/ | San Francisco, New York City, and US remote | Full TimeSelected job postings here (all compensation in annual base salary range for SF/NY hubs):- Engineering Director - Machine Learning ($280,000—$381,000 USD): https://boards.greenhouse.io/figma/jobs/4953079004- Engineering Director - Server Platform ($282,000—$410,000 USD): https://boards.greenhouse.io/figma/jobs/4868741004- ML/AI Engineer ($168,000—$350,000 USD): https://boards.greenhouse.io/figma/jobs/4756707004- Software Engineer - FigJam ($168,000—$350,000 USD): https://boards.greenhouse.io/figma/jobs/4339815004===Born on the Web, Figma helps entire product teams brainstorm, create, test, and ship better designs, together. From great products to long-lasting companies, we believe that nothing great is made alone. Come make with us!Figma recently made 200 fixes and improvements to Dev Mode: https://news.ycombinator.com/item?id=37226227Keeping Figma fast — perf-testing the WASM editor: https://news.ycombinator.com/item?id=37324121
            """
        self.example_entities_1 = json.dumps([{
            'job title': 'Engineering Director - Machine Learning',
            'salary': '$280,000—$381,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4953079004',
        }, 
        {
            'job title': 'Engineering Director - Server Platform',
            'salary': '$282,000—$410,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4868741004',
        },
        {
            'job title': 'ML/AI Engineer',
            'salary': '$168,000—$350,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4756707004',
        },
        {
            'job title': 'Software Engineer',
            'salary': '$168,000—$350,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4339815004',
        }])
        self.example_text_2 = """
            Kanary | Backend Engineering Lead | Seattle, Remote (US or Canada) PST Preferred | Comp Estimate: $150k base + 3% EquityWe’re using large scale browser automation and LLMs to scrub your private info (home address, phone number, emails) off the public internet.We’re a team of 5, backed by top pre-seed VCs like YC and 2048 and privacy leaders like Mozilla. 2 years since our first raise, we’re funded by our customers.Titles at our stage don’t matter much. We’re looking for a strong engineer to help grow the product and the team as we respond to rapid customer growth. The most challenging work at Kanary is backend development. You’ll own projects like:- experiment with novel approaches for anonymously traversing the web (captcha solving, browser fingerprinting, residential IPs). Embrace the cat and mouse game of working against the bad guys.
            """
        self.example_entities_2 = json.dumps({
            'job title': 'Backend Engineering Lead',
            'salary': '$150k base + 3% Equity',
            'company': 'Kanary',
            'company location': 'Seattle',
            'remote': 'Yes',
            'link to apply': None,
        })
        self.example_text_3 = """
            What an impactful project! I'm applying for your Product Engineer role, but I also wanted to share a page I made for you on my site highlighting a few reasons I think I'd be a great fit.You can see it here:https://www.theothermelissa.com/for-Emily-at-CommunityPhone"""

        self.example_entities_3 = ""

    def extract(self, content):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_role},
                {"role": "user", "content":  self.example_text_1},
                {"role": "assistant", "content":  self.example_entities_1},
                {"role": "user", "content":  self.example_text_2},
                {"role": "assistant", "content":  self.example_entities_2},
                {"role": "user", "content":  self.example_text_3},
                {"role": "assistant", "content":  self.example_entities_3},
                {"role": "user", "content": content},
            ],
            temperature=1.0,
            max_tokens=500,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            timeout=40
        )
        try:
            return json.loads(response["choices"][0]["message"]["content"])
        except json.decoder.JSONDecodeError:
            print("Couldn't parse JSON from model response")
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

