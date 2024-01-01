import json

import openai


class ChatExtractor:
    def __init__(self, model_key=None, model=None, max_tokens=500):
        if model_key:
            self.model_key = model_key
        else:
            raise ValueError("No OpenAI API key provided")
        if model:
            self.model = model
        else:
            raise ValueError("No OpenAI API model provided")
        self.max_tokens = max_tokens
        self.model = model
        self.system_role = """You are a helpful assistant that extracts the key points of a job posting designed to output JSON.
      
        Instructions:
            - Be concise and only include key points of salary, location, remote/on-onsite, company name, company location, link to apply, languages and frameworks
            - Use lowercase,
            - Don't use line breaks.
            - If it isn't an comment for a company hiring, then `salary` should be `None`.
            - Return a flat map of items - DO NOT return a list with nested children.
            """
        self.example_text_1 = """
            {
             "245": "Figma | https://www.figma.com/ | San Francisco, New York City, and US remote | Full TimeSelected job postings here (all compensation in annual base salary range for SF/NY hubs):- Engineering Director - Machine Learning ($280,000—$381,000 USD): https://boards.greenhouse.io/figma/jobs/4953079004- Engineering Director - Server Platform ($282,000—$410,000 USD): https://boards.greenhouse.io/figma/jobs/4868741004- ML/AI Engineer ($168,000—$350,000 USD): https://boards.greenhouse.io/figma/jobs/4756707004- Software Engineer - FigJam ($168,000—$350,000 USD): https://boards.greenhouse.io/figma/jobs/4339815004===Born on the Web, Figma helps entire product teams brainstorm, create, test, and ship better designs, together. From great products to long-lasting companies, we believe that nothing great is made alone. Come make with us!Figma recently made 200 fixes and improvements to Dev Mode: https://news.ycombinator.com/item?id=37226227Keeping Figma fast — perf-testing the WASM editor: https://news.ycombinator.com/item?id=37324121",
             "246": "SmarterDx | 180 - 230K + equity + benefits | Remote first (but U.S. only due to data confidentiality) | Full time We are an early stage health tech company using AI to improve hospital revenue cycle (making healthcare costs lower and allowing doctors to focus on patient care). The team is small but high functioning (MD + data scientist combos, former ASF board member, Google and Amazon engineers, Stanford LLM researchers, etc.) and initially scaled the company to $1MM+ in contracted revenue without raising capital.We have been backed by top investors including Floodgate (Lyft, Twitch, Twitter), Bessemer, and are currently on pace to 30X in revenue over a two-year time period.Who we are looking for:- Data scientists- ML Ops- FS Eng (Senior and Staff)- Product designer- Technical PM (not listed yet on careers but we are hiring for this!)Be part of the journey as we hone our PMF and build to scale! For more, see: https://smarterdx.com/careers If interested email us at hiring at smarterdx dot com"
            }

            """
        self.example_entities_1 = json.dumps([{
            'index': '245',
            'job title': 'Engineering Director - Machine Learning',
            'salary': '$280,000—$381,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4953079004',
        }, 
        {
            'index': '245',
            'job title': 'Engineering Director - Server Platform',
            'salary': '$282,000—$410,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4868741004',
        },
        {
            'index': '245',
            'job title': 'ML/AI Engineer',
            'salary': '$168,000—$350,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4756707004',
        },
        {
            'index': '245',
            'job title': 'Software Engineer',
            'salary': '$168,000—$350,000 USD',
            'company': 'Figma',
            'company location': 'San Francisco, New York City',
            'remote': 'Yes',
            'link to apply': 'https://boards.greenhouse.io/figma/jobs/4339815004',
        },
        {
            'index': '246',
            'job title': 'Data scientists',
            'salary': '180 - 230K + equity + benefits',
            'company': 'SmarterDx',
            'company location': 'Unknown',
            'remote': 'Yes (but U.S. only due to data confidentiality)',
            'link to apply': 'https://smarterdx.com/careers',
        },
        {
            'index': '246',
            'job title': 'ML Ops',
            'salary': '180 - 230K + equity + benefits',
            'company': 'SmarterDx',
            'company location': 'Unknown',
            'remote': 'Yes (but U.S. only due to data confidentiality)',
            'link to apply': 'https://smarterdx.com/careers',
        },
        {
            'index': '246',
            'job title': 'FS Eng (Senior and Staff)',
            'salary': '180 - 230K + equity + benefits',
            'company': 'SmarterDx',
            'company location': 'Unknown',
            'remote': 'Yes (but U.S. only due to data confidentiality)',
            'link to apply': 'https://smarterdx.com/careers',
        },
        {
            'index': '246',
            'job title': 'Product designer',
            'salary': '180 - 230K + equity + benefits',
            'company': 'SmarterDx',
            'company location': 'Unknown',
            'remote': 'Yes (but U.S. only due to data confidentiality)',
            'link to apply': 'https://smarterdx.com/careers',
        },
        {
            'index': '246',
            'job title': 'Technical PM',
            'salary': '180 - 230K + equity + benefits',
            'company': 'SmarterDx',
            'company location': 'Unknown',
            'remote': 'Yes (but U.S. only due to data confidentiality)',
            'link to apply': 'https://smarterdx.com/careers',
        },
        ])
        self.example_text_2 = """
            { 
                "20": "Kanary | Backend Engineering Lead | Seattle, Remote (US or Canada) PST Preferred | Comp Estimate: $150k base + 3% EquityWe’re using large scale browser automation and LLMs to scrub your private info (home address, phone number, emails) off the public internet.We’re a team of 5, backed by top pre-seed VCs like YC and 2048 and privacy leaders like Mozilla. 2 years since our first raise, we’re funded by our customers.Titles at our stage don’t matter much. We’re looking for a strong engineer to help grow the product and the team as we respond to rapid customer growth. The most challenging work at Kanary is backend development. You’ll own projects like:- experiment with novel approaches for anonymously traversing the web (captcha solving, browser fingerprinting, residential IPs). Embrace the cat and mouse game of working against the bad guys.",
                "84": "NetFoundry | $115k to 180k base comp | Full-time | REMOTE | USA | DevRel LeaderYou are responsible for building the OpenZiti developer community. This is initially an IC role; you will then build out a DevRel team.The open source OpenZiti platform enables developers to embed zero trust, full mesh networking into their solutions, as software. Example:https://github.com/openziti-test-kitchen/go-httpOpenZiti delivers billions of zero trust sessions per year for leaders around the world.  NetFoundry originated OpenZiti, is the maintainer and sells CloudZiti SaaS (hosted OpenZiti). NetFoundry is a remote-first company.You are a good candidate if you love to learn about the problems, opportunities, constraints, hopes and fears of the developer, operations and security communities which you will serve.More info:https://netfoundry.io/careers/devrel-leader/"
            }
            """
        self.example_entities_2 = json.dumps([{
            'index': '20',
            'job title': 'Backend Engineering Lead',
            'salary': '$150k base + 3% Equity',
            'company': 'Kanary',
            'company location': 'Seattle',
            'remote': 'Yes',
            'link to apply': None,
        },
        {
            'index': '84',
            'job title': 'DevRel Leader',
            'salary': '$115k to 180k base comp ',
            'company': 'NetFoundry',
            'company location': 'USA',
            'remote': 'Yes',
            'link to apply': 'https://netfoundry.io/careers/devrel-leader/',
        },
        ])
        self.example_text_3 = """
            { "30": "What an impactful project! I'm applying for your Product Engineer role, but I also wanted to share a page I made for you on my site highlighting a few reasons I think I'd be a great fit.You can see it here:https://www.theothermelissa.com/for-Emily-at-CommunityPhone" } """

        self.example_entities_3 = ""

    def extract(self, content):
        try:
            content = json.dumps(content)
        except Exception:
            print(f"Couldn't convert to JSON")
            raise

        openai.api_key = self.model_key
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
            temperature=0.0,
            max_tokens=self.max_tokens,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            timeout=40,
            response_format={"type": "json_object"},
        )
        try:
            response = response["choices"]
            response = response[0]["message"]["content"]
            return json.loads(response)
        except json.decoder.JSONDecodeError:
            print("Couldn't parse JSON from model response")
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

