import os
from rich import print
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.github_read import parse_github_url, get_pull_request, get_issue

load_dotenv()

prompt =  """You are a GitHub assistant for maintainers.
 
You will be given a GitHub URL. Use the tools to fetch it, then respond.
 
If it is a pull request, reply in markdown with:
1. Summary (2-3 sentences)
2. Risks or bugs you noticed
3. Suggestions for the author
4. Verdict: approve / request changes / needs discussion
 
If it is an issue, reply in markdown with:
1. Summary
2. Type: bug / feature / question
3. Suggested labels
4. Suggested priority (low / medium / high) with a one-line reason
 
Only use information returned by the tools. If something is missing, say so."""


def Agent():
    model = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

    return create_agent(
        model= model,
        tools=[get_issue, get_pull_request],
        system_prompt=prompt,
        name="Github Assistant"
    )


def review(url: str) -> str:
    owner, repo, kind, number = parse_github_url(url = url)
    prompt = f"Review this {kind}: owner={owner}, repo={repo}, number={number}"

    result = Agent().invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )
    print(result)
    content = result["messages"][-1].content
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content

print(review(url="https://github.com/HimmatMagar/revision_repo/pull/2"))